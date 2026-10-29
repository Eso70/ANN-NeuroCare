"""Service checks do not need a browser event loop or a running database."""
from unittest.mock import Mock

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import OperationalError

from app.schemas.prediction import PredictionInput
from app.services.predictions import create_prediction
from tests.fixtures import PAYLOAD


def sample():
    return PredictionInput(**PAYLOAD)


def test_service_saves_version_and_original_inputs():
    session, predictor = Mock(), Mock()
    session.refresh.side_effect = lambda record: setattr(record, "id", 9)
    predictor.threshold = 0.5
    predictor.predict.return_value = (1, 0.75, "unit-test")
    result = create_prediction(sample(), session, predictor)
    assert result.id == 9
    record = session.add.call_args.args[0]
    assert record.input_data == sample().model_dump()
    assert record.model_version == "unit-test"
    session.commit.assert_called_once()


def test_accuracy_policy_notice_is_returned_with_the_actual_saved_result():
    session, predictor = Mock(), Mock()
    session.refresh.side_effect = lambda record: setattr(record, "id", 10)
    predictor.threshold = 0.49
    predictor.predict.return_value = (0, 0.25, "accuracy-policy-test")
    predictor.metadata = {"operating_point_notice": "Accuracy is prioritized; positive labels may be missed."}
    result = create_prediction(sample(), session, predictor)
    assert "not a diagnosis" in result.notice
    assert "positive labels may be missed" in result.notice
    assert result.model_version == "accuracy-policy-test"
    session.commit.assert_called_once()


def test_service_rolls_back_failed_persistence():
    session, predictor = Mock(), Mock()
    predictor.threshold = 0.5
    predictor.predict.return_value = (0, 0.25, "unit-test")
    session.commit.side_effect = OperationalError("query", {}, Exception("database down"))
    with pytest.raises(OperationalError):
        create_prediction(sample(), session, predictor)
    session.rollback.assert_called_once()


@pytest.mark.parametrize("change", [{"Age": -1}, {"Age": 3.5}, {"BMI": float("nan")}, {"name": "private"}])
def test_input_contract_rejects_invalid_values(change):
    with pytest.raises(ValidationError):
        PredictionInput(**{**sample().model_dump(), **change})
