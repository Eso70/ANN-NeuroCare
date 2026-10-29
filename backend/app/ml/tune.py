"""Version a frozen ANN with a validation-selected cutoff; never retrains the ANN."""
import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
from sklearn.linear_model import LogisticRegression

from app.ml.data import read_dataset
from app.ml.evaluation import binary_metrics, select_validation_threshold
from app.ml.inference import Predictor


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", required=True, type=Path)
    parser.add_argument("--csv", required=True, type=Path)
    args = parser.parse_args()
    predictor = Predictor(args.model_dir)
    parent = predictor.metadata
    if hashlib.sha256(args.csv.read_bytes()).hexdigest() != parent["dataset_sha256"]:
        raise ValueError("Dataset does not match saved training split")
    rows, labels = read_dataset(args.csv)
    with np.load(args.model_dir / "split_indices.npz", allow_pickle=False) as saved:
        splits = {name: saved[name].copy() for name in ("train", "validation", "test")}
    combined = np.concatenate(list(splits.values()))
    if not np.array_equal(np.sort(combined), np.arange(len(rows))):
        raise ValueError("Saved split is not a complete disjoint row partition")
    profiles = {name: {tuple(rows[i]) for i in indices} for name, indices in splits.items()}
    if profiles["train"] & profiles["validation"] or profiles["train"] & profiles["test"] or profiles["validation"] & profiles["test"]:
        raise ValueError("Profile leakage across saved splits")

    def inputs(name):
        return np.asarray(predictor.preprocessing.transform([rows[i] for i in splits[name]]), dtype="float32")

    targets = {name: [labels[i] for i in indices] for name, indices in splits.items()}
    validation = inputs("validation")
    validation_scores = predictor.model(validation, training=False).numpy().reshape(-1)
    threshold = select_validation_threshold(targets["validation"], validation_scores)
    # Freeze selection before loading/evaluating the test inputs.
    selection = {"split": "validation", "objective": "maximum F2", "beta": 2,
                 "tie_break": "highest threshold", "rows": len(validation),
                 "test_used_for_selection": False}
    baseline = LogisticRegression(max_iter=500, random_state=parent["seed"])
    baseline.fit(inputs("train"), targets["train"])
    baseline_threshold = select_validation_threshold(
        targets["validation"], baseline.predict_proba(validation)[:, 1]
    )
    test = inputs("test")
    test_scores = predictor.model(test, training=False).numpy().reshape(-1)
    metadata = dict(parent)
    metadata.update({
        "format_version": 3,
        "version": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8],
        "parent_version": parent["version"], "threshold": threshold,
        "threshold_selection": selection,
        "validation_metrics": binary_metrics(targets["validation"], validation_scores, threshold),
        "test_metrics": binary_metrics(targets["test"], test_scores, threshold),
        "reference_test_metrics_at_0_5": binary_metrics(targets["test"], test_scores, 0.5),
        "baseline_metrics": {
            "logistic_regression": binary_metrics(targets["test"], baseline.predict_proba(test)[:, 1], baseline_threshold),
            "logistic_regression_threshold": baseline_threshold,
            "majority_class_accuracy": max(targets["test"].count(0), targets["test"].count(1)) / len(test),
        },
        "evaluation_note": "Same Phase 3 test partition was previously reported. Threshold chosen only on validation data; this comparison is not a new independent validation.",
    })
    directory = args.model_dir.resolve().parent / metadata["version"]
    directory.mkdir(exist_ok=False)
    for name in ("model.keras", "split_indices.npz"):
        shutil.copyfile(args.model_dir / name, directory / name)
    (directory / "metadata.json").write_text(json.dumps(metadata, indent=2, allow_nan=False), encoding="utf-8")
    print(f"Saved {directory}; ANN weights unchanged; validation-selected threshold {threshold:.6f}")
    print(json.dumps(metadata["test_metrics"], indent=2))


if __name__ == "__main__":
    main()
