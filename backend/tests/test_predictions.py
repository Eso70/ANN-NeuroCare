from unittest.mock import Mock
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.api.routes.predictions import get_predictor
from app.db.session import get_db
from app.main import app
from app.ml.inference import ModelUnavailable

from tests.fixtures import PAYLOAD


@pytest.fixture
def dependencies():
    session = Mock()
    session.refresh.side_effect = lambda record: setattr(record, "id", 7)
    predictor = Mock()
    predictor.threshold = 0.5
    predictor.predict.return_value = (1, 0.75, "test-model")
    app.dependency_overrides[get_db] = lambda: session
    app.dependency_overrides[get_predictor] = lambda: predictor
    yield TestClient(app), session, predictor
    app.dependency_overrides.clear()


def test_prediction_saved_before_success(dependencies):
    client, session, predictor = dependencies
    response = client.post("/api/v1/predictions", json=PAYLOAD)
    assert response.status_code == 201
    assert response.json()["id"] == 7
    assert response.json()["predicted_probability"] == 0.75
    session.commit.assert_called_once()
    predictor.predict.assert_called_once_with(PAYLOAD)


@pytest.mark.parametrize("change", [{"Age": -1}, {"Age": 1.5}, {"BMI": -1}, {"name": "private"}])
def test_invalid_input_never_persisted(dependencies, change):
    client, session, predictor = dependencies
    assert client.post("/api/v1/predictions", json={**PAYLOAD, **change}).status_code == 422
    session.commit.assert_not_called()
    predictor.predict.assert_not_called()


def test_validation_errors_name_fields_without_echoing_values(dependencies):
    client, session, predictor = dependencies
    response = client.post("/api/v1/predictions", json={**PAYLOAD, "Age": 40, "BMI": "private-input-value"})
    assert response.status_code == 422
    errors = {item["field"]: item["message"] for item in response.json()["errors"]}
    assert "13" in errors["Age"]
    assert "integer" in errors["BMI"].lower()
    assert "private-input-value" not in response.text
    assert "input" not in response.json()["errors"][0]
    session.commit.assert_not_called()
    predictor.predict.assert_not_called()


def test_unknown_fields_do_not_echo_arbitrary_names(dependencies):
    client, _, _ = dependencies
    response = client.post("/api/v1/predictions", json={**PAYLOAD, "private-extra-field": "private-value"})
    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] == "request"
    assert "private-extra-field" not in response.text
    assert "private-value" not in response.text


def test_missing_field_and_invalid_json_errors_are_safe(dependencies):
    client, _, _ = dependencies
    response = client.post("/api/v1/predictions", json={key: value for key, value in PAYLOAD.items() if key != "BMI"})
    assert response.status_code == 422
    assert response.json()["errors"] == [{"field": "BMI", "message": "Field required"}]
    response = client.post("/api/v1/predictions", content="not-json-private", headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] == "request"
    assert "not-json-private" not in response.text


def test_model_unavailable(dependencies):
    client, session, _ = dependencies

    def unavailable():
        raise ModelUnavailable()

    app.dependency_overrides[get_predictor] = unavailable
    assert client.post("/api/v1/predictions", json=PAYLOAD).status_code == 503
    session.commit.assert_not_called()


def test_database_failure_rolls_back(dependencies):
    client, session, _ = dependencies
    session.commit.side_effect = OperationalError("private", {}, Exception("password"))
    response = client.post("/api/v1/predictions", json=PAYLOAD)
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
    session.rollback.assert_called_once()


@pytest.mark.integration
def test_real_model_and_prediction_persistence():
    if os.environ.get("RUN_ML_TESTS") != "1":
        pytest.skip("Set RUN_ML_TESTS=1 with a trained MODEL_DIR and migrated PostgreSQL")
    from app.db.session import SessionLocal
    from app.models import Prediction

    response = TestClient(app).post("/api/v1/predictions", json=PAYLOAD)
    assert response.status_code == 201, response.text
    data = response.json()
    with SessionLocal() as session:
        record = session.get(Prediction, data["id"])
        try:
            assert record is not None
            assert record.input_data == PAYLOAD
            assert record.model_version == data["model_version"]
            assert record.predicted_probability == data["predicted_probability"]
        finally:
            if record is not None:
                session.delete(record)
                session.commit()


@pytest.mark.integration
def test_prediction_history_survives_new_sessions():
    if os.environ.get("RUN_ML_TESTS") != "1":
        pytest.skip("Set RUN_ML_TESTS=1 with configured model and migrated PostgreSQL")
    from sqlalchemy import select
    from app.db.session import SessionLocal
    from app.models import Prediction

    identifiers = []
    try:
        with TestClient(app) as client:
            for bmi in (25, 30):
                response = client.post("/api/v1/predictions", json={**PAYLOAD, "BMI": bmi})
                assert response.status_code == 201, response.text
                identifiers.append(response.json()["id"])
        with SessionLocal() as session:
            history = session.scalars(select(Prediction).where(Prediction.id.in_(identifiers)).order_by(Prediction.id)).all()
            assert [row.id for row in history] == identifiers
            assert [row.input_data["BMI"] for row in history] == [25, 30]
            assert all(row.created_at and row.model_version for row in history)
        with SessionLocal() as session:
            assert session.get(Prediction, identifiers[0]) is not None
    finally:
        with SessionLocal() as session:
            for identifier in identifiers:
                record = session.get(Prediction, identifier)
                if record is not None:
                    session.delete(record)
            session.commit()
