import numpy as np
import pandas as pd
import pytest

from app.ml.brfss2021 import RECODE, convert_frame
from app.ml.data import FEATURES, TARGET, Preprocessor
from app.ml.train_2021 import adapt_first_layer, cross_year_splits
from tests.fixtures import PAYLOAD


def raw_frame(count=1):
    row = {source: next(iter(mapping)) for source, mapping in RECODE.values()}
    row.update({"_BMI5": 2750, "IYEAR": b"2021", "MENTHLTH": 88, "PHYSHLTH": 88})
    return pd.DataFrame([dict(row) for _ in range(count)])


def test_recode_valid_zero_days_income_and_implied_decimal_bmi():
    frame = raw_frame(4)
    frame["INCOME3"] = [8, 9, 10, 11]
    converted, _ = convert_frame(frame)
    assert len(converted) == 4
    assert converted["Income"].tolist() == [8, 8, 8, 8]
    assert converted["BMI"].tolist() == [28] * 4
    assert converted["MentHlth"].tolist() == [0] * 4
    assert converted["PhysHlth"].tolist() == [0] * 4
    assert converted.columns.tolist() == [*FEATURES, TARGET]


def test_diabetes_mapping_is_explicit_and_does_not_merge_prediabetes_with_yes():
    frame = raw_frame(6)
    frame["DIABETE4"] = [1, 2, 3, 4, 7, 9]
    converted, invalid = convert_frame(frame)
    assert converted[TARGET].tolist() == [1, 0, 0, 0]
    assert invalid[TARGET] == 2


@pytest.mark.parametrize("column,unknown", [("INCOME3", 77), ("INCOME3", 99), ("MENTHLTH", 77),
                                           ("_HLTHPLN", 9), ("_FRTLT1A", 9), ("TOLDHI3", np.nan)])
def test_unknown_responses_are_excluded_instead_of_becoming_no(column, unknown):
    frame = raw_frame(2)
    frame.loc[0, column] = unknown
    converted, _ = convert_frame(frame)
    assert converted.index.tolist() == [1]


def test_reversed_indicators_and_never_checked_cholesterol():
    frame = raw_frame(2)
    frame["_RFHYPE6"] = [1, 2]
    frame["_RFDRHV7"] = [1, 2]
    frame["_HLTHPLN"] = [1, 2]
    frame["_CHOLCH3"] = [1, 3]
    frame["SEXVAR"] = [1, 2]
    converted, _ = convert_frame(frame)
    assert converted["HighBP"].tolist() == [0, 1]
    assert converted["HvyAlcoholConsump"].tolist() == [0, 1]
    assert converted["AnyHealthcare"].tolist() == [1, 0]
    assert converted["CholCheck"].tolist() == [1, 0]
    assert converted["Sex"].tolist() == [1, 0]


def test_wrong_wave_and_missing_columns_are_rejected():
    frame = raw_frame()
    frame["IYEAR"] = b"2015"
    with pytest.raises(ValueError, match="year"):
        convert_frame(frame)
    with pytest.raises(ValueError, match="Missing"):
        convert_frame(raw_frame().drop(columns=["_BMI5"]))


def test_first_layer_rescaling_preserves_transferred_function():
    rng = np.random.default_rng(4)
    raw = rng.normal(size=(30, 21))
    kernel, bias = rng.normal(size=(21, 5)), rng.normal(size=5)
    old = Preprocessor(rng.normal(size=21).tolist(), rng.uniform(0.5, 3, 21).tolist())
    new = Preprocessor(rng.normal(size=21).tolist(), rng.uniform(0.5, 3, 21).tolist())
    adjusted_kernel, adjusted_bias = adapt_first_layer(kernel, bias, old, new)
    expected = ((raw - old.means) / old.scales) @ kernel + bias
    measured = ((raw - new.means) / new.scales) @ adjusted_kernel + adjusted_bias
    np.testing.assert_allclose(measured, expected, atol=1e-12, rtol=1e-12)


def test_cross_year_holdouts_are_new_and_prior_training_matches_stay_in_training():
    def row(i, physical):
        values = {**PAYLOAD, "BMI": 20 + i % 30, "MentHlth": i % 31, "PhysHlth": physical}
        return [values[name] for name in FEATURES]
    old = [row(i, 20) for i in range(20)]
    fresh = [row(i, i // 31) for i in range(150)]
    source = old + fresh
    rows, _, splits, indices, report = cross_year_splits(source, [i % 2 for i in range(len(source))], old,
        {"train": np.arange(10), "validation": np.arange(10, 15), "test": np.arange(15, 20)})
    assert report["quarantined_prior_heldout_profile_rows"] == 10
    assert report["prior_training_profile_rows_forced_to_training"] == 10
    assert set(indices).isdisjoint(range(10, 20))
    profiles = {tuple(values) for values in old}
    for split in ("validation", "test"):
        assert not profiles & {tuple(rows[i]) for i in splits[split]}
    assert set(range(len(rows))) == set(np.concatenate(list(splits.values())))


def test_experimental_year_cannot_silently_use_the_legacy_public_contract(monkeypatch):
    from types import SimpleNamespace
    from app.api.routes import predictions
    from app.ml.data import CONTRACT_2021
    from app.ml.inference import ModelUnavailable

    monkeypatch.setattr(predictions, "load_predictor", lambda _: SimpleNamespace(metadata={"contract_id": CONTRACT_2021}))
    with pytest.raises(ModelUnavailable, match="offline-only"):
        predictions.get_predictor()


def test_legacy_training_refuses_a_different_year_manifest(monkeypatch, tmp_path, capsys):
    import json
    import sys
    from app.ml import train
    from app.ml.data import CONTRACT_2021

    csv = tmp_path / "year2021.csv"
    csv.with_suffix(".json").write_text(json.dumps({"contract_id": CONTRACT_2021}))
    monkeypatch.setattr(sys, "argv", ["train", "--csv", str(csv), "--source", "CDC 2021"])
    with pytest.raises(SystemExit) as stopped:
        train.main()
    assert stopped.value.code == 2
    assert "app.ml.train_2021" in capsys.readouterr().err


def test_invalid_parent_partitions_fail_before_new_data_is_split():
    row = [PAYLOAD[name] for name in FEATURES]
    with pytest.raises(ValueError, match="exactly once"):
        cross_year_splits([], [], [row], {"train": np.array([0]), "validation": np.array([0]), "test": np.array([], dtype=int)})
    with pytest.raises(ValueError, match="overlap"):
        cross_year_splits([], [], [row, row], {"train": np.array([0]), "validation": np.array([], dtype=int), "test": np.array([1])})
