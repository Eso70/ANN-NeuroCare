"""Fresh-wave comparison: new 2021 training, old-profile quarantine and frozen test.

Does not modify .env or auto-promote a candidate. See docs/brfss2021-training-plan.md.
"""
import argparse
import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

os.environ.setdefault("TF_DETERMINISTIC_OPS", "1")
os.environ.setdefault("TF_NUM_INTEROP_THREADS", "2")
os.environ.setdefault("TF_NUM_INTRAOP_THREADS", "4")

import numpy as np

from app.ml.brfss2021 import CODEBOOK_URL, SOURCE_URL
from app.ml.data import CONTRACT_ID, CONTRACT_2021, FEATURES, TARGET, TARGET_2021, Preprocessor, read_dataset, split_indices
from app.ml.evaluation import binary_metrics, select_recall_constrained_threshold
from app.ml.inference import Predictor


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def cross_year_splits(rows, labels, old_rows, old_splits):
    """Prior held-out profiles are excluded; prior train profiles stay train-only."""
    indices = np.concatenate([old_splits[name] for name in ("train", "validation", "test")])
    if not np.array_equal(np.sort(indices), np.arange(len(old_rows))):
        raise ValueError("Parent splits must cover every historical row exactly once")
    profiles = {name: {tuple(old_rows[i]) for i in old_splits[name]} for name in ("train", "validation", "test")}
    if any(profiles[a] & profiles[b] for a, b in (("train", "validation"), ("train", "test"), ("validation", "test"))):
        raise ValueError("Parent feature profiles overlap across splits")
    old_train = profiles["train"]
    old_all = {tuple(row) for row in old_rows}
    forbidden = old_all - old_train
    source_indices = [i for i, row in enumerate(rows) if tuple(row) not in forbidden]
    cohort = [rows[i] for i in source_indices]
    y = [labels[i] for i in source_indices]
    forced = [i for i, row in enumerate(cohort) if tuple(row) in old_train]
    novel = [i for i, row in enumerate(cohort) if tuple(row) not in old_all]
    train, validation, test = split_indices([cohort[i] for i in novel], [y[i] for i in novel], 42)
    novel = np.asarray(novel)
    splits = {"train": np.concatenate((novel[train], np.asarray(forced, dtype=int))),
              "validation": novel[validation], "test": novel[test]}
    for name in ("validation", "test"):
        if any(tuple(cohort[i]) in old_all for i in splits[name]):
            raise ValueError("Prior profile leakage into fresh held-out rows")
    return cohort, y, splits, np.asarray(source_indices), {
        "quarantined_prior_heldout_profile_rows": len(rows) - len(cohort),
        "prior_training_profile_rows_forced_to_training": len(forced),
        "novel_profile_rows": len(novel), "fresh_holdout_profile_overlap_with_2015": 0,
    }


def adapt_first_layer(kernel, bias, previous, current):
    """Preserve the warm-start function when moving to new training-only scaling."""
    ratio = np.asarray(current.scales) / previous.scales
    offset = (np.asarray(current.means) - previous.means) / previous.scales
    return (kernel * ratio[:, None]).astype(kernel.dtype), (bias + offset @ kernel).astype(bias.dtype)


def grouped_accuracy_interval(rows, labels, old_scores, old_threshold, new_scores, new_threshold):
    """Paired profile-cluster bootstrap; describes this held-out cohort only."""
    difference = ((new_scores >= new_threshold) == labels).astype(int) - ((old_scores >= old_threshold) == labels).astype(int)
    mapping, totals = {}, []
    for row, value in zip(rows, difference):
        key = tuple(row)
        if key not in mapping:
            mapping[key] = len(totals)
            totals.append([0, 0])
        total = totals[mapping[key]]
        total[0] += int(value)
        total[1] += 1
    totals = np.asarray(totals)
    rng = np.random.default_rng(42)
    samples = []
    for _ in range(2000):
        selected = rng.integers(0, len(totals), len(totals))
        sums = totals[selected].sum(axis=0)
        samples.append(float(sums[0] / sums[1]))
    return {"method": "paired bootstrap of identical-feature-profile clusters; 2000 draws; seed 42",
            "accuracy_delta_95_percent_interval": np.percentile(samples, [2.5, 97.5]).tolist()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--old-csv", required=True, type=Path)
    parser.add_argument("--parent", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=Path("../artifacts"))
    parser.add_argument("--epochs", type=int, default=60)
    args = parser.parse_args()
    if not 1 <= args.epochs <= 200:
        parser.error("epochs must be between 1 and 200")
    import sklearn
    import tensorflow as tf
    from sklearn.linear_model import LogisticRegression

    parent = Predictor(args.parent.resolve())
    if parent.metadata["contract_id"] != CONTRACT_ID or parent.architecture != {"hidden_units": [64, 32], "dropout_rates": [0.1, 0.1]}:
        raise ValueError("This comparison expects the preserved 2015 64/32 ANN with dropout 0.1")
    if digest(args.old_csv) != parent.metadata["dataset_sha256"]:
        raise ValueError("Parent dataset checksum mismatch")
    source_manifest = json.loads(args.csv.with_suffix(".json").read_text(encoding="utf-8"))
    if source_manifest["contract_id"] != CONTRACT_2021 or digest(args.csv) != source_manifest["csv_sha256"]:
        raise ValueError("Converted 2021 data provenance mismatch")
    old_rows, _ = read_dataset(args.old_csv)
    rows, labels = read_dataset(args.csv)
    with np.load(args.parent / "split_indices.npz", allow_pickle=False) as saved:
        old_splits = {name: saved[name].copy() for name in ("train", "validation", "test")}
    rows, labels, splits, source_indices, overlap = cross_year_splits(rows, labels, old_rows, old_splits)
    print("Cross-year split audit:", json.dumps(overlap), flush=True)
    del old_rows
    version = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    directory = args.output.resolve() / version
    directory.mkdir(parents=True, exist_ok=False)
    print("Experiment directory:", directory, flush=True)
    cohort_csv = directory / "training_cohort.csv"
    with cohort_csv.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow([*FEATURES, TARGET])
        writer.writerows([*[int(v) for v in row], label] for row, label in zip(rows, labels))
    np.savez_compressed(directory / "split_indices.npz", **splits)
    np.savez_compressed(directory / "cohort_source_indices.npz", indices=source_indices)
    raw_train = [rows[i] for i in splits["train"]]
    raw_validation = [rows[i] for i in splits["validation"]]
    preprocessing = Preprocessor.fit(raw_train)
    train, validation = [np.asarray(preprocessing.transform(values), dtype="float32") for values in (raw_train, raw_validation)]
    y_train, y_validation = [np.asarray([labels[i] for i in splits[name]], dtype="float32") for name in ("train", "validation")]

    def predict(model, values):
        return np.concatenate([model(values[i:i + 2048], training=False).numpy().reshape(-1)
                               for i in range(0, len(values), 2048)])

    parent_validation = np.asarray(parent.preprocessing.transform(raw_validation), dtype="float32")
    old_val_scores = predict(parent.model, parent_validation)
    old_val_metrics = binary_metrics(y_validation, old_val_scores, parent.threshold)
    minimum_recall = max(0.8, old_val_metrics["recall"])
    parent_threshold = select_recall_constrained_threshold(y_validation, old_val_scores, minimum_recall)
    print(f"Frozen validation recall floor: {minimum_recall:.8f}", flush=True)
    logistic = LogisticRegression(max_iter=500, random_state=42).fit(train, y_train)
    logistic_threshold = select_recall_constrained_threshold(y_validation, logistic.predict_proba(validation)[:, 1], minimum_recall)
    protocol = {"parent_version": parent.version, "parent_dataset_sha256": digest(args.old_csv),
                "source_csv_sha256": digest(args.csv), "cohort_sha256": digest(cohort_csv),
                "overlap": overlap, "selection": "maximum validation accuracy, then average precision, then lower Brier",
                "minimum_recall": minimum_recall, "test_used_for_selection": False,
                "parent_original_validation_metrics": old_val_metrics, "parent_adapted_threshold": parent_threshold,
                "trials": []}
    write_json(directory / "search.json", protocol)
    options = tf.data.Options()
    options.threading.private_threadpool_size = 2
    validation_data = tf.data.Dataset.from_tensor_slices((validation, y_validation)).batch(2048).with_options(options)
    best, best_key = None, None
    configs = [
        {"name": "fresh_2021", "units": [64, 32], "dropout": 0.1, "l2": 0.0001, "learning_rate": 0.001},
        {"name": "transfer_2021", "units": [64, 32], "dropout": 0.1, "l2": 0.0001, "learning_rate": 0.0001},
    ]
    for config in configs:
        tf.keras.utils.set_random_seed(42)
        if config["name"] == "fresh_2021":
            layers = [tf.keras.layers.Input(shape=(len(FEATURES),))]
            for width in config["units"]:
                layers.extend([tf.keras.layers.Dense(width, activation="relu", kernel_regularizer=tf.keras.regularizers.L2(config["l2"])), tf.keras.layers.Dropout(config["dropout"])])
            layers.append(tf.keras.layers.Dense(1, activation="sigmoid", bias_initializer=tf.keras.initializers.Constant(float(np.log(y_train.mean() / (1 - y_train.mean()))))))
            model = tf.keras.Sequential(layers)
        else:
            model = tf.keras.models.clone_model(parent.model)
            model.set_weights(parent.model.get_weights())
            first = next(layer for layer in model.layers if isinstance(layer, tf.keras.layers.Dense))
            first.set_weights(adapt_first_layer(*first.get_weights(), parent.preprocessing, preprocessing))
            np.testing.assert_allclose(predict(model, validation[:256]), old_val_scores[:256], atol=1e-6, rtol=2e-5)
        model.compile(optimizer=tf.keras.optimizers.Adam(config["learning_rate"]), loss="binary_crossentropy")
        train_data = tf.data.Dataset.from_tensor_slices((train, y_train)).shuffle(len(train), seed=42).batch(512).with_options(options).prefetch(1)
        print("Training", config["name"], flush=True)
        history = model.fit(train_data, validation_data=validation_data, shuffle=False, epochs=args.epochs, verbose=2, callbacks=[
            tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=3, min_lr=0.00001),
            tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=8, restore_best_weights=True),
        ])
        scores = predict(model, validation)
        threshold = select_recall_constrained_threshold(y_validation, scores, minimum_recall)
        metrics = binary_metrics(y_validation, scores, threshold)
        trial = {"configuration": config, "threshold": threshold, "validation_metrics": metrics,
                 "epochs_completed": len(history.history["loss"]),
                 "history": {name: [float(v) for v in values] for name, values in history.history.items()}}
        key = (metrics["accuracy"], metrics["average_precision"], -metrics["brier_score"])
        if best_key is None or key > best_key:
            best, best_key = trial, key
            model.save(directory / "model.keras")
        protocol["trials"].append(trial)
        write_json(directory / "search.json", protocol)
        print("Validation:", json.dumps(metrics), flush=True)

    write_json(directory / "frozen_selection.json", {"configuration": best["configuration"], "threshold": best["threshold"],
               "model_sha256": digest(directory / "model.keras"), "minimum_recall": minimum_recall,
               "frozen_at_utc": datetime.now(timezone.utc).isoformat(), "test_evaluated": False})
    # First test inference happens only after the selection file has been written.
    winner = tf.keras.models.load_model(directory / "model.keras", compile=False, safe_mode=True)
    raw_test = [rows[i] for i in splits["test"]]
    test = np.asarray(preprocessing.transform(raw_test), dtype="float32")
    y_test = np.asarray([labels[i] for i in splits["test"]])
    scores = predict(winner, test)
    old_scores = predict(parent.model, np.asarray(parent.preprocessing.transform(raw_test), dtype="float32"))
    metrics = binary_metrics(y_test, scores, best["threshold"])
    baseline = binary_metrics(y_test, old_scores, parent_threshold)
    original = binary_metrics(y_test, old_scores, parent.threshold)
    interval = grouped_accuracy_interval(raw_test, y_test, old_scores, parent_threshold, scores, best["threshold"])
    metadata = {
        "format_version": 3, "version": version, "contract_id": CONTRACT_2021, "features": list(FEATURES), "target": TARGET_2021,
        "threshold": best["threshold"], "threshold_selection": {"split": "validation", "objective": "maximum accuracy subject to recall floor",
             "minimum_recall": minimum_recall, "test_used_for_selection": False, "rows": len(validation), "tie_break": "higher recall, then higher threshold"},
        "parent_version": parent.version, "source": f"CDC BRFSS 2021; {SOURCE_URL}; {CODEBOOK_URL}",
        "dataset_year": 2021, "dataset_file": "training_cohort.csv", "dataset_sha256": digest(cohort_csv),
        "source_csv_sha256": digest(args.csv), "raw_source_sha256": source_manifest["source_sha256"],
        "model_sha256": digest(directory / "model.keras"), "preprocessing": preprocessing.to_dict(),
        "split_sizes": {name: len(indices) for name, indices in splits.items()}, "seed": 42,
        "split_method": "5 stratified profile-group folds among novel 2021 profiles; prior training matches forced to train; prior heldout matches quarantined",
        "cross_year_overlap": overlap, "class_counts": {str(i): labels.count(i) for i in (0, 1)},
        "unique_profiles": len({tuple(row) for row in rows}), "epochs_completed": best["epochs_completed"],
        "training_configuration": best["configuration"], "training": {"optimizer": "Adam", "loss": "binary_crossentropy", "batch_size": 512,
             "max_epochs": args.epochs, "early_stopping_patience": 8, "restore_best_weights": True, "lr_schedule": "halve after 3 plateau epochs; minimum 1e-5",
             "initialization": "parent weights with first-layer scaling adaptation" if best["configuration"]["name"] == "transfer_2021" else "fresh weights; training class log odds output bias"},
        "class_weighting": "none; natural class frequencies; no survey weights", "validation_metrics": best["validation_metrics"], "test_metrics": metrics,
        "baseline_metrics": {"majority_class_accuracy": float(max((y_test == 0).mean(), (y_test == 1).mean())),
             "previous_ann": baseline, "previous_ann_threshold": parent_threshold, "previous_ann_original_cutoff": original,
             "logistic_regression": binary_metrics(y_test, logistic.predict_proba(test)[:, 1], logistic_threshold), "logistic_regression_threshold": logistic_threshold},
        "dependencies": {"tensorflow": tf.__version__, "numpy": np.__version__, "sklearn": sklearn.__version__},
        "evaluation_note": "Fresh 2021 test profiles absent from the entire old dataset. Both model and cutoff selected using validation only. Subject identity not verified; not clinical validation.",
        "limitations": "Educational unweighted complete-case survey classifier; no clinical validity or individual risk calibration. Nominal 2021 income; changed survey questions and selection bias limit cross-year comparisons.",
    }
    write_json(directory / "metadata.json", metadata)
    comparison = {"parent_version": parent.version, "candidate_version": version, "same_test_rows": len(y_test),
                  "baseline_metrics": baseline, "candidate_metrics": metrics, "parent_original_cutoff_metrics": original,
                  "accuracy_delta": metrics["accuracy"] - baseline["accuracy"], "recall_delta": metrics["recall"] - baseline["recall"],
                  "promotion_eligible_by_predeclared_metric_gate": metrics["accuracy"] > baseline["accuracy"] and metrics["recall"] >= baseline["recall"],
                  **interval, "test_used_for_selection": False, "environment_changed": False}
    write_json(directory / "comparison.json", comparison)
    print(json.dumps(comparison, indent=2), flush=True)
    print("Candidate saved. Active configuration and original artifacts remain unchanged.", flush=True)


if __name__ == "__main__":
    main()
