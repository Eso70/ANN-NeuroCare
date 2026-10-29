"""A separate, validation-selected accuracy operating point; never edits .env."""
import argparse
import copy
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np

from app.ml.data import read_dataset
from app.ml.evaluation import binary_metrics, select_accuracy_target_threshold, select_maximum_accuracy_threshold
from app.ml.inference import Predictor
from app.ml.train_2021 import digest, write_json


def create_accuracy_candidate(parent_directory, output, target=0.85, buffer=0.005):
    parent = Predictor(parent_directory)
    csv = parent_directory / "training_cohort.csv"
    if digest(csv) != parent.metadata["dataset_sha256"]:
        raise ValueError("Parent cohort checksum mismatch")
    rows, labels = read_dataset(csv)
    with np.load(parent_directory / "split_indices.npz", allow_pickle=False) as saved:
        splits = {name: saved[name] for name in ("train", "validation", "test")}

    def scores(name):
        values = np.asarray(parent.preprocessing.transform([rows[i] for i in splits[name]]), dtype="float32")
        return np.concatenate([parent.model(values[i:i + 2048], training=False).numpy().reshape(-1)
                               for i in range(0, len(values), 2048)])

    y_validation = np.asarray([labels[i] for i in splits["validation"]])
    validation_scores = scores("validation")
    fallback = False
    try:
        threshold = select_accuracy_target_threshold(y_validation, validation_scores, target + buffer)
        policy = {"objective": "maximum recall subject to accuracy floor", "minimum_accuracy": target + buffer}
    except ValueError as error:
        if "accuracy floor" not in str(error):
            raise
        # Establish feasibility using validation only; then maximize validation accuracy.
        select_accuracy_target_threshold(y_validation, validation_scores, target)
        threshold = select_maximum_accuracy_threshold(y_validation, validation_scores)
        policy = {"objective": "maximum validation accuracy"}
        fallback = True
    policy.update({"split": "validation", "requested_accuracy": target,
                   "requested_buffer": buffer, "buffer_infeasible": fallback,
                   "test_used_for_selection": False, "rows": len(y_validation),
                   "tie_break": "higher recall, then higher threshold"})
    validation_metrics = binary_metrics(y_validation, validation_scores, threshold)
    version = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    directory = output.resolve() / version
    directory.mkdir(parents=True, exist_ok=False)
    for filename in ("model.keras", "split_indices.npz", "training_cohort.csv", "cohort_source_indices.npz"):
        shutil.copy2(parent_directory / filename, directory / filename)
    frozen = {"threshold": threshold, "policy": policy, "model_sha256": digest(directory / "model.keras"),
              "dataset_sha256": digest(csv), "validation_metrics": validation_metrics,
              "frozen_at_utc": datetime.now(timezone.utc).isoformat(), "test_evaluated": False}
    write_json(directory / "frozen_selection.json", frozen)
    print("Frozen accuracy policy:", json.dumps(frozen), flush=True)
    # No test inference above this point. The cutoff is never adjusted below.
    y_test = np.asarray([labels[i] for i in splits["test"]])
    test_scores = scores("test")
    metrics = binary_metrics(y_test, test_scores, threshold)
    before = binary_metrics(y_test, test_scores, parent.threshold)
    majority = float(max((y_test == 0).mean(), (y_test == 1).mean()))
    eligible = metrics["accuracy"] >= target and metrics["accuracy"] > majority and metrics["recall"] > 0
    metadata = copy.deepcopy(parent.metadata)
    metadata.update({"version": version, "parent_version": parent.version, "threshold": threshold,
                     "threshold_selection": policy, "validation_metrics": validation_metrics,
                     "test_metrics": metrics, "deployment_status": "accuracy_target_candidate",
                     "weights_changed": False,
                     "evaluation_note": "Previously evaluated 2021 partitions. User requested an accuracy-first operating point. Cutoff selected on validation only; learned weights unchanged. Not fresh independent validation.",
                     "operating_point_notice": "Overall accuracy is prioritized. Many positive survey labels are missed; review recall alongside accuracy."})
    metadata["baseline_metrics"]["previous_policy_same_weights"] = before
    metadata["baseline_metrics"]["reference_note"] = "Original reference models retain their recall-focused cutoffs; majority baseline uses identical test rows."
    write_json(directory / "metadata.json", metadata)
    report = {"version": version, "parent_version": parent.version, "model_weights_unchanged": True,
              "test_rows": len(y_test), "validation_metrics": validation_metrics,
              "previous_cutoff_metrics": before, "accuracy_policy_metrics": metrics,
              "majority_class_accuracy": majority, "eligible_for_review": eligible,
              "threshold": threshold, "test_used_for_selection": False,
              "fresh_independent_validation": False, "environment_changed": False}
    write_json(directory / "comparison.json", report)
    print("Candidate directory:", directory, flush=True)
    print(json.dumps(report, indent=2), flush=True)
    return directory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=Path("../artifacts"))
    args = parser.parse_args()
    create_accuracy_candidate(args.parent.resolve(), args.output)


if __name__ == "__main__":
    main()
