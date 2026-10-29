"""Public source semantics for supported, explicitly reviewed model artifacts."""
from copy import deepcopy
import math

from app.ml.data import CONTRACT_ID, CONTRACT_2021, FIELD_SPECS, TARGET_DESCRIPTION, TARGET_2021


def _unit_interval(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and 0 <= value <= 1)


def _reviewed_recall_policy(metadata):
    """Project review guard, not a clinical standard or future-performance promise.

    Selection uses validation only. Test recall is a deployment review check, never
    a reason to adjust the saved cutoff. Accuracy-first experiments stay offline.
    """
    validation = metadata.get("validation_metrics")
    test = metadata.get("test_metrics")
    policy = metadata.get("threshold_selection")
    if not all(isinstance(value, dict) for value in (validation, test, policy)):
        return False
    floor = policy.get("minimum_recall")
    numbers = (floor, validation.get("recall"), test.get("recall"),
               validation.get("accuracy"), test.get("accuracy"))
    return (metadata.get("deployment_status") == "recall_policy_reviewed"
            and all(_unit_interval(value) for value in numbers)
            and floor >= 0.8 and validation["recall"] >= floor and test["recall"] >= 0.8
            and policy.get("objective") == "maximum accuracy subject to recall floor"
            and policy.get("split") == "validation"
            and policy.get("test_used_for_selection") is False)


def contract_for_model(metadata=None):
    if metadata is not None and not isinstance(metadata, dict):
        raise ValueError("Unsupported public model metadata")
    metadata = metadata or {}
    contract_id = metadata.get("contract_id", CONTRACT_ID)
    if contract_id == CONTRACT_ID:
        year = 2015
        target = TARGET_DESCRIPTION
        source_url = "https://www.kaggle.com/datasets/alexteboul/diabetes-health-indicators-dataset"
        codebook = "https://www.cdc.gov/brfss/annual_data/2015/pdf/codebook15_llcp.pdf"
        note = "Stored binary survey label; precise historical source recoding remains unverified."
    elif contract_id == CONTRACT_2021:
        if not _reviewed_recall_policy(metadata):
            raise ValueError("Configured model uses an offline-only dataset contract")
        year = 2021
        target = TARGET_2021
        source_url = "https://www.cdc.gov/brfss/annual_data/annual_2021.html"
        codebook = "https://www.cdc.gov/brfss/annual_data/2021/pdf/codebook21_llcp-v2-508.pdf"
        note = "DIABETE4 yes=1; no, pregnancy-only and borderline/prediabetes=0; unknown/refused excluded."
    else:
        raise ValueError("Unsupported public dataset contract")
    fields = deepcopy(FIELD_SPECS)
    if year == 2021:
        next(field for field in fields if field["name"] == "Income")["label"] = "Annual household income (2021 nominal USD)"
    return {"contract_id": contract_id, "fields": fields, "target": target,
            "dataset": {"year": year, "name": f"CDC BRFSS {year}", "source_url": source_url,
                        "codebook_url": codebook, "income_units": f"{year} nominal USD",
                        "target_note": note}}
