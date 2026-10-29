import pytest

from app.ml.contracts import contract_for_model
from app.ml.data import CONTRACT_ID, CONTRACT_2021, FEATURES, FIELD_SPECS


def reviewed():
    return {"contract_id": CONTRACT_2021, "deployment_status": "recall_policy_reviewed",
            "threshold_selection": {"objective": "maximum accuracy subject to recall floor",
                                    "split": "validation", "minimum_recall": 0.83,
                                    "test_used_for_selection": False},
            "validation_metrics": {"accuracy": 0.67, "recall": 0.84},
            "test_metrics": {"accuracy": 0.67, "recall": 0.82}}


def test_reviewed_source_year_changes_labels_without_changing_numeric_inputs():
    result = contract_for_model(reviewed())
    assert result["dataset"]["year"] == 2021
    assert "DIABETE4" in result["target"]
    assert [field["name"] for field in result["fields"]] == list(FEATURES)
    income = next(field for field in result["fields"] if field["name"] == "Income")
    assert "2021 nominal USD" in income["label"] and income["max"] == 8
    original_income = next(field for field in FIELD_SPECS if field["name"] == "Income")
    assert "2015" in original_income["label"]
    assert income["options"] == original_income["options"]


def test_legacy_and_unconfigured_contracts_remain_available():
    assert contract_for_model()["contract_id"] == CONTRACT_ID
    assert contract_for_model({"contract_id": CONTRACT_ID})["dataset"]["year"] == 2015


@pytest.mark.parametrize("change", [{"recall": 0.1395}, {"recall": 0}, {"accuracy": float("nan")}, {"accuracy": True}])
def test_review_marker_cannot_enable_invalid_or_low_recall_metrics(change):
    metadata = reviewed()
    metadata["test_metrics"].update(change)
    with pytest.raises(ValueError, match="offline-only"):
        contract_for_model(metadata)


@pytest.mark.parametrize("change", [
    {"minimum_recall": 0.79}, {"minimum_recall": True}, {"minimum_recall": float("nan")},
    {"minimum_recall": 0.85}, {"split": "test"}, {"test_used_for_selection": True},
    {"test_used_for_selection": None}, {"objective": "maximum validation accuracy"},
])
def test_review_cannot_bypass_validation_selection_or_recall_floor(change):
    metadata = reviewed()
    metadata["threshold_selection"].update(change)
    with pytest.raises(ValueError, match="offline-only"):
        contract_for_model(metadata)


@pytest.mark.parametrize("metrics", [None, [], {"accuracy": 0.7, "recall": 0.8},
                                     {"accuracy": 0.7, "recall": float("nan")}])
def test_missing_or_failed_validation_metrics_are_blocked(metrics):
    metadata = reviewed()
    metadata["validation_metrics"] = metrics
    with pytest.raises(ValueError, match="offline-only"):
        contract_for_model(metadata)


def test_retired_accuracy_first_review_does_not_enable_public_inference():
    metadata = reviewed()
    metadata.update({"deployment_status": "accuracy_target_reviewed",
                     "test_metrics": {"accuracy": 0.85, "recall": 0.14},
                     "threshold_selection": {"objective": "maximum validation accuracy"}})
    with pytest.raises(ValueError, match="offline-only"):
        contract_for_model(metadata)


def test_api_predictor_dependency_enforces_review_before_inference(monkeypatch):
    from types import SimpleNamespace

    from app.api.routes import predictions
    from app.ml.inference import ModelUnavailable

    predictor = SimpleNamespace(metadata=reviewed())
    monkeypatch.setattr(predictions, "load_predictor", lambda _: predictor)
    assert predictions.get_predictor() is predictor
    predictor.metadata["test_metrics"]["recall"] = 0.1395
    with pytest.raises(ModelUnavailable, match="offline-only"):
        predictions.get_predictor()


def test_unknown_or_unreviewed_contracts_are_not_served():
    with pytest.raises(ValueError):
        contract_for_model({"contract_id": "unknown"})
    with pytest.raises(ValueError, match="offline-only"):
        contract_for_model({"contract_id": CONTRACT_2021})


def test_returned_fields_are_isolated_from_global_contract_mutation():
    result = contract_for_model()
    result["fields"][0]["max"] = 99
    assert contract_for_model()["fields"][0]["max"] == 1
