"""Recheck fresh-wave artifact integrity, source lineage and prior-profile exclusion."""
import argparse
import json
from pathlib import Path

import numpy as np

from app.ml.audit import audit_model
from app.ml.data import read_dataset
from app.ml.evaluation import binary_metrics, select_recall_constrained_threshold
from app.ml.inference import Predictor
from app.ml.train_2021 import digest, write_json


def audit_2021(directory, csv, old_csv, parent_directory, raw):
    metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
    search = json.loads((directory / "search.json").read_text(encoding="utf-8"))
    frozen = json.loads((directory / "frozen_selection.json").read_text(encoding="utf-8"))
    source = json.loads(csv.with_suffix(".json").read_text(encoding="utf-8"))
    if digest(raw) != source["source_sha256"] or digest(csv) != metadata["source_csv_sha256"]:
        raise ValueError("2021 raw or converted data checksum mismatch")
    if digest(old_csv) != search["parent_dataset_sha256"]:
        raise ValueError("Historical dataset checksum mismatch")
    if digest(directory / "model.keras") != frozen["model_sha256"] or frozen["threshold"] != metadata["threshold"]:
        raise ValueError("Frozen model or threshold changed after selection")
    rows, labels = read_dataset(directory / "training_cohort.csv")
    source_rows, source_labels = read_dataset(csv)
    old_rows, _ = read_dataset(old_csv)
    with np.load(directory / "cohort_source_indices.npz", allow_pickle=False) as saved:
        indices = saved["indices"]
    if len(indices) != len(rows) or len(set(indices.tolist())) != len(indices) or indices.min() < 0 or indices.max() >= len(source_rows):
        raise ValueError("Invalid source row lineage")
    if any(rows[i] != source_rows[j] or labels[i] != source_labels[j] for i, j in enumerate(indices)):
        raise ValueError("Cohort does not match the converted source rows")
    with np.load(parent_directory / "split_indices.npz", allow_pickle=False) as saved:
        prior = {name: saved[name] for name in ("train", "validation", "test")}
    np.testing.assert_array_equal(np.sort(np.concatenate(list(prior.values()))), np.arange(len(old_rows)))
    old_profiles = {name: {tuple(old_rows[i]) for i in values} for name, values in prior.items()}
    if any(old_profiles[a] & old_profiles[b] for a, b in (("train", "validation"), ("train", "test"), ("validation", "test"))):
        raise ValueError("Parent profile partitions overlap")
    forbidden = old_profiles["validation"] | old_profiles["test"]
    all_old = forbidden | old_profiles["train"]
    expected = [i for i, row in enumerate(source_rows) if tuple(row) not in forbidden]
    np.testing.assert_array_equal(indices, expected)
    with np.load(directory / "split_indices.npz", allow_pickle=False) as saved:
        splits = {name: saved[name] for name in ("train", "validation", "test")}
    for name in ("validation", "test"):
        if any(tuple(rows[i]) in all_old for i in splits[name]):
            raise ValueError("Fresh holdout includes a historical profile")
    if any(tuple(rows[i]) in forbidden for i in splits["train"]):
        raise ValueError("New training contains a prior held-out profile")
    report = audit_model(directory, directory / "training_cohort.csv")
    parent = Predictor(parent_directory)

    def parent_scores(name):
        transformed = np.asarray(parent.preprocessing.transform([rows[i] for i in splits[name]]), dtype="float32")
        return np.concatenate([parent.model(transformed[i:i + 2048], training=False).numpy().reshape(-1)
                               for i in range(0, len(transformed), 2048)])

    val_labels = [labels[i] for i in splits["validation"]]
    val_scores = parent_scores("validation")
    floor = max(0.8, binary_metrics(val_labels, val_scores, parent.threshold)["recall"])
    np.testing.assert_allclose(floor, search["minimum_recall"], atol=1e-12)
    threshold = select_recall_constrained_threshold(val_labels, val_scores, floor)
    np.testing.assert_allclose(threshold, metadata["baseline_metrics"]["previous_ann_threshold"], atol=1e-7)
    baseline = binary_metrics([labels[i] for i in splits["test"]], parent_scores("test"), threshold)
    for name, expected_value in metadata["baseline_metrics"]["previous_ann"].items():
        np.testing.assert_allclose(baseline[name], expected_value, rtol=1e-6, atol=1e-7, err_msg=name)
    comparison = json.loads((directory / "comparison.json").read_text(encoding="utf-8"))
    measured = report["recomputed_test_metrics"]
    eligible = measured["accuracy"] > baseline["accuracy"] and measured["recall"] >= baseline["recall"]
    if eligible != comparison["promotion_eligible_by_predeclared_metric_gate"]:
        raise ValueError("Promotion comparison does not match audited metrics")
    report.update({"source_lineage_matches": True, "raw_source_checksum_matches": True,
                   "cross_year_fresh_holdout_profile_overlap": 0,
                   "historical_heldout_profiles_excluded_from_training": True,
                   "parent_2021_metrics_recomputed": baseline,
                   "frozen_selection_matches_artifact": True,
                   "promotion_eligible_by_predeclared_metric_gate": eligible})
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("model", "csv", "old-csv", "parent", "raw", "output"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    args = parser.parse_args()
    report = audit_2021(args.model.resolve(), args.csv.resolve(), args.old_csv.resolve(), args.parent.resolve(), args.raw.resolve())
    write_json(args.output, report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
