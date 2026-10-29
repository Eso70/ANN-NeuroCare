"""Recompute a saved model's split, scaling, threshold, and test metrics without fitting."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from app.core.config import ROOT, get_settings
from app.ml.data import read_dataset
from app.ml.evaluation import (
    binary_metrics, select_accuracy_target_threshold, select_maximum_accuracy_threshold,
    select_recall_constrained_threshold, select_validation_threshold,
)
from app.ml.inference import Predictor


def audit_model(directory: Path, csv: Path) -> dict:
    predictor = Predictor(directory)
    metadata = predictor.metadata
    digest = hashlib.sha256(csv.read_bytes()).hexdigest()
    if digest != metadata["dataset_sha256"]:
        raise ValueError("Dataset checksum does not match model provenance")
    rows, labels = read_dataset(csv)
    with np.load(directory / "split_indices.npz", allow_pickle=False) as saved:
        splits = {name: saved[name].copy() for name in ("train", "validation", "test")}
    if not np.array_equal(np.sort(np.concatenate(list(splits.values()))), np.arange(len(rows))):
        raise ValueError("Split indices do not partition every row exactly once")
    profiles = {name: {tuple(rows[i]) for i in indices} for name, indices in splits.items()}
    if profiles["train"] & profiles["validation"] or profiles["train"] & profiles["test"] or profiles["validation"] & profiles["test"]:
        raise ValueError("Identical feature profiles occur across splits")
    values = np.asarray(rows, dtype="float64")
    training = values[splits["train"]]
    # Independent NumPy calculations check the persisted statistics produced by statistics.mean/pstdev.
    scales = training.std(axis=0)
    scales[scales == 0] = 1
    np.testing.assert_allclose(predictor.preprocessing.means, training.mean(axis=0), atol=1e-12, rtol=1e-12)
    np.testing.assert_allclose(predictor.preprocessing.scales, scales, atol=1e-12, rtol=1e-12)

    def scores(name):
        transformed = predictor.preprocessing.transform([rows[i] for i in splits[name]])
        return predictor.model(np.asarray(transformed, dtype="float32"), training=False).numpy().reshape(-1)

    validation_labels = [labels[i] for i in splits["validation"]]
    if metadata.get("threshold_selection"):
        policy = metadata["threshold_selection"]
        validation_scores = scores("validation")
        if policy["objective"] == "maximum F2":
            selected = select_validation_threshold(validation_labels, validation_scores)
        elif policy["objective"] == "maximum accuracy subject to recall floor":
            selected = select_recall_constrained_threshold(validation_labels, validation_scores, policy["minimum_recall"])
        elif policy["objective"] == "maximum recall subject to accuracy floor":
            selected = select_accuracy_target_threshold(validation_labels, validation_scores, policy["minimum_accuracy"])
        elif policy["objective"] == "maximum validation accuracy":
            selected = select_maximum_accuracy_threshold(validation_labels, validation_scores)
        else:
            raise ValueError("Unknown threshold selection policy")
        np.testing.assert_allclose(predictor.threshold, selected, rtol=0, atol=1e-7)
        if metadata.get("validation_metrics"):
            measured = binary_metrics(validation_labels, validation_scores, predictor.threshold)
            for name, expected in metadata["validation_metrics"].items():
                np.testing.assert_allclose(measured[name], expected, rtol=1e-6, atol=1e-7, err_msg=name)
    computed = binary_metrics([labels[i] for i in splits["test"]], scores("test"), predictor.threshold)
    for name, expected in metadata["test_metrics"].items():
        np.testing.assert_allclose(computed[name], expected, rtol=1e-6, atol=1e-7, err_msg=name)
    return {
        "model_version": predictor.version, "dataset_sha256": digest, "rows": len(rows),
        "partition_covers_all_rows_once": True, "cross_split_profile_overlap": 0,
        "saved_scaling_matches_training_only_statistics": True,
        "threshold_matches_validation_selection": bool(metadata.get("threshold_selection")),
        "threshold": predictor.threshold,
        "split_sizes": {name: len(indices) for name, indices in splits.items()},
        "recomputed_test_metrics": computed,
        "saved_test_metrics_match": True,
        "limitation": metadata.get("evaluation_note", "Previously reported test partition; no new independent validation. Survey-profile grouping is not a verified person identifier."),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--model", type=Path, help="Audit a candidate without changing MODEL_DIR")
    args = parser.parse_args()
    directory = args.model.resolve() if args.model else get_settings().model_dir
    if directory is None:
        parser.error("Configure MODEL_DIR before auditing")
    csv = args.csv
    if csv is None:
        metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
        filename = metadata.get("dataset_file")
        if filename:
            if not isinstance(filename, str) or Path(filename).name != filename or Path(filename).is_absolute():
                parser.error("Model dataset_file must be a plain filename")
            csv = directory / filename
        else:
            csv = ROOT / "data/diabetes_binary_health_indicators_BRFSS2015.csv"
    report = audit_model(directory, csv)
    if args.output:
        args.output.write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
