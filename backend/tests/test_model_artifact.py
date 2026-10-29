import json
import os

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.ml.data import FEATURES, SUPPORTED_CONTRACTS
from app.ml.inference import ModelUnavailable, Predictor, load_predictor
from app.api.routes.predictions import model_contract, model_details
from tests.fixtures import PAYLOAD
from app.main import app


@pytest.fixture
def artifact():
    if os.environ.get("RUN_MODEL_TESTS") != "1":
        pytest.skip("Set RUN_MODEL_TESTS=1 with a locally trained CDC model")
    return get_settings().model_dir


def test_saved_model_reload_and_contract(artifact):
    first, second = Predictor(artifact), Predictor(artifact)
    label, score, version = first.predict(PAYLOAD)
    assert label in (0, 1) and 0 <= score <= 1
    assert label == int(score >= first.threshold)
    assert second.predict(PAYLOAD)[1] == pytest.approx(score, abs=1e-7)
    assert first.metadata["contract_id"] in SUPPORTED_CONTRACTS
    assert model_contract()["contract_id"] == first.metadata["contract_id"]
    assert model_details(first)["version"] == version
    assert model_details(first)["architecture"] == first.architecture
    if first.metadata.get("training_configuration"):
        assert first.architecture["hidden_units"] == first.metadata["training_configuration"]["units"]
    assert model_details(first)["threshold_selection"] == first.metadata.get("threshold_selection")
    assert [item["name"] for item in model_contract()["fields"]] == list(FEATURES)


def test_legacy_model_rejected(artifact, tmp_path):
    metadata = json.loads((artifact / "metadata.json").read_text())
    metadata["format_version"] = 1
    (tmp_path / "metadata.json").write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match="contract"):
        Predictor(tmp_path)


def test_unconfigured_or_missing_model_fails_explicitly(tmp_path):
    for directory in (None, tmp_path):
        with pytest.raises(ModelUnavailable):
            load_predictor(directory)


def test_incomplete_artifact_returns_service_unavailable(tmp_path):
    from app.api.routes.predictions import get_predictor

    (tmp_path / "metadata.json").write_text("{}")
    app.dependency_overrides[get_predictor] = lambda: load_predictor(tmp_path)
    try:
        response = TestClient(app).post("/api/v1/predictions", json=PAYLOAD)
        assert response.status_code == 503
        assert response.json()["detail"].startswith("Model unavailable")
        assert str(tmp_path) not in response.text
    finally:
        app.dependency_overrides.clear()


def test_changed_model_hash_rejected(artifact, tmp_path):
    saved = json.loads((artifact / "metadata.json").read_text())
    (tmp_path / "metadata.json").write_text(json.dumps(saved))
    (tmp_path / "model.keras").write_bytes(b"damaged-model-fixture")
    with pytest.raises(ValueError, match="checksum"):
        Predictor(tmp_path)


@pytest.mark.parametrize("threshold", [0, 1, float("nan"), True])
def test_invalid_artifact_threshold_rejected(artifact, tmp_path, threshold):
    saved = json.loads((artifact / "metadata.json").read_text())
    saved["threshold"] = threshold
    (tmp_path / "metadata.json").write_text(json.dumps(saved))
    with pytest.raises(ValueError, match="threshold"):
        Predictor(tmp_path)


def test_contract_endpoint_requires_no_model():
    response = TestClient(app).get("/api/v1/model/contract")
    assert response.status_code == 200
    fields = {item["name"]: item for item in response.json()["fields"]}
    assert len(fields) == 21 and fields["Age"]["max"] == 13
    assert "Glucose" not in fields


def test_metadata_endpoint_matches_saved_evaluation(artifact):
    saved = json.loads((artifact / "metadata.json").read_text())
    response = TestClient(app).get("/api/v1/model")
    assert response.status_code == 200
    assert response.json()["test_metrics"] == saved["test_metrics"]
    assert response.json()["baseline_metrics"] == saved["baseline_metrics"]
    assert response.json()["threshold"] == saved["threshold"]
