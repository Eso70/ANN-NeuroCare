"""Bounded ANN search on training/validation data; evaluate only the frozen winner.

Never changes .env or the parent artifact. Run from backend with --help.
"""
import argparse
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

from app.ml.data import read_dataset
from app.ml.evaluation import binary_metrics, select_recall_constrained_threshold
from app.ml.inference import Predictor


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--parent", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=Path("../artifacts"))
    parser.add_argument("--epochs", type=int, default=60)
    args = parser.parse_args()
    if not 1 <= args.epochs <= 200:
        parser.error("epochs must be between 1 and 200")

    import tensorflow as tf

    parent = Predictor(args.parent.resolve())
    digest = hashlib.sha256(args.csv.read_bytes()).hexdigest()
    if digest != parent.metadata["dataset_sha256"]:
        raise ValueError("Use the parent's exact dataset to preserve the comparison")
    rows, labels = read_dataset(args.csv)
    with np.load(args.parent / "split_indices.npz", allow_pickle=False) as saved:
        splits = {name: saved[name].copy() for name in ("train", "validation", "test")}
    if not np.array_equal(np.sort(np.concatenate(list(splits.values()))), np.arange(len(rows))):
        raise ValueError("Invalid parent split partition")
    profiles = {name: {tuple(rows[i]) for i in indices} for name, indices in splits.items()}
    if any(profiles[a] & profiles[b] for a, b in (("train", "validation"), ("train", "test"), ("validation", "test"))):
        raise ValueError("Parent splits contain overlapping feature profiles")
    preprocessing = parent.preprocessing
    # Confirm parent statistics were fitted on training rows only.
    raw_train = np.asarray([rows[i] for i in splits["train"]])
    scales = raw_train.std(axis=0)
    scales[scales == 0] = 1
    np.testing.assert_allclose(preprocessing.means, raw_train.mean(axis=0), rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(preprocessing.scales, scales, rtol=1e-12, atol=1e-12)
    train, validation = [np.asarray(preprocessing.transform([rows[i] for i in splits[name]]), dtype="float32")
                         for name in ("train", "validation")]
    y_train, y_validation = [np.asarray([labels[i] for i in splits[name]], dtype="float32")
                             for name in ("train", "validation")]

    def predict(model, values):
        return np.concatenate([model(values[i:i + 2048], training=False).numpy().reshape(-1)
                               for i in range(0, len(values), 2048)])

    original_validation = binary_metrics(y_validation, predict(parent.model, validation), parent.threshold)
    minimum_recall = original_validation["recall"]
    version = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    directory = args.output.resolve() / version
    directory.mkdir(parents=True, exist_ok=False)
    print(f"Experiment directory: {directory}", flush=True)
    print(f"Frozen validation recall floor: {minimum_recall:.8f}", flush=True)

    candidates = [
        {"name": "wide", "units": [64, 32], "dropout": 0.1, "l2": 0.0001, "learning_rate": 0.001},
        {"name": "deep", "units": [128, 64, 32], "dropout": 0.15, "l2": 0.0001, "learning_rate": 0.0005},
        {"name": "compact", "units": [32, 16], "dropout": 0.05, "l2": 0.00001, "learning_rate": 0.001},
    ]
    options = tf.data.Options()
    options.threading.private_threadpool_size = 2
    train_data = (tf.data.Dataset.from_tensor_slices((train, y_train))
                  .shuffle(len(train), seed=42, reshuffle_each_iteration=True)
                  .batch(512).with_options(options).prefetch(1))
    validation_data = tf.data.Dataset.from_tensor_slices((validation, y_validation)).batch(2048).with_options(options)
    trials = []
    best = None
    best_key = None
    for config in candidates:
        tf.keras.utils.set_random_seed(42)
        layers = [tf.keras.layers.Input(shape=(train.shape[1],))]
        for units in config["units"]:
            layers.extend([tf.keras.layers.Dense(units, activation="relu", kernel_regularizer=tf.keras.regularizers.L2(config["l2"])),
                           tf.keras.layers.Dropout(config["dropout"])])
        bias = float(np.log(y_train.mean() / (1 - y_train.mean())))
        layers.append(tf.keras.layers.Dense(1, activation="sigmoid", bias_initializer=tf.keras.initializers.Constant(bias)))
        model = tf.keras.Sequential(layers)
        model.compile(optimizer=tf.keras.optimizers.Adam(config["learning_rate"]), loss="binary_crossentropy")
        print(f"Training {config['name']}: {config}", flush=True)
        history = model.fit(train_data, validation_data=validation_data, epochs=args.epochs, verbose=2, shuffle=False, callbacks=[
            tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=3, min_lr=0.00001),
            tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=8, restore_best_weights=True),
        ])
        scores = predict(model, validation)
        threshold = select_recall_constrained_threshold(y_validation, scores, minimum_recall)
        metrics = binary_metrics(y_validation, scores, threshold)
        trial = {"configuration": config, "epochs_completed": len(history.history["loss"]),
                 "threshold": threshold, "validation_metrics": metrics,
                 "history": {name: [float(x) for x in values] for name, values in history.history.items()}}
        trials.append(trial)
        key = (metrics["accuracy"], metrics["average_precision"], -metrics["brier_score"])
        if best_key is None or key > best_key:
            best_key, best = key, trial
            model.save(directory / "model.keras")
        write_json(directory / "search.json", {"parent_version": parent.version, "original_validation_metrics": original_validation,
                   "minimum_recall": minimum_recall, "selection": "validation accuracy, then average precision, then lower Brier score",
                   "test_used_for_selection": False, "trials": trials})
        print(f"Validation {config['name']}: {json.dumps(metrics)}", flush=True)

    # Winner/configuration/cutoff are frozen BEFORE any test inference.
    winner = tf.keras.models.load_model(directory / "model.keras", compile=False, safe_mode=True)
    test = np.asarray(preprocessing.transform([rows[i] for i in splits["test"]]), dtype="float32")
    y_test = [labels[i] for i in splits["test"]]
    metrics = binary_metrics(y_test, predict(winner, test), best["threshold"])
    np.savez_compressed(directory / "split_indices.npz", **splits)
    metadata = dict(parent.metadata)
    for key in ("reference_test_metrics_at_0_5",):
        metadata.pop(key, None)
    metadata.update({
        "version": version, "parent_version": parent.version,
        "model_sha256": hashlib.sha256((directory / "model.keras").read_bytes()).hexdigest(),
        "threshold": best["threshold"],
        "threshold_selection": {"split": "validation", "objective": "maximum accuracy subject to recall floor",
                                "minimum_recall": minimum_recall, "tie_break": "higher recall, then higher threshold",
                                "rows": len(validation), "test_used_for_selection": False},
        "validation_metrics": best["validation_metrics"], "test_metrics": metrics,
        "epochs_completed": best["epochs_completed"], "training_configuration": best["configuration"],
        "training": {"optimizer": "Adam", "loss": "binary_crossentropy", "batch_size": 512, "max_epochs": args.epochs,
                     "early_stopping_patience": 8, "restore_best_weights": True,
                     "lr_schedule": "halve after 3 epochs without validation loss improvement; minimum 1e-5",
                     "output_bias": "training class log odds", "seed": 42},
        "candidate_selection": {"candidates": len(trials), "split": "validation", "objective": "accuracy at parent validation recall floor"},
        "dependencies": {**parent.metadata["dependencies"], "tensorflow": tf.__version__, "numpy": np.__version__},
        "evaluation_note": "Previously reported parent test partition. Three candidate configurations and cutoff selected using training/validation only. Not a new independent validation.",
    })
    write_json(directory / "metadata.json", metadata)
    comparison = {"parent_version": parent.version, "candidate_version": version, "parent_test_metrics": parent.metadata["test_metrics"],
                  "candidate_test_metrics": metrics, "validation_recall_floor": minimum_recall,
                  "validation_selected_configuration": best["configuration"], "test_used_for_selection": False,
                  "accuracy_delta": metrics["accuracy"] - parent.metadata["test_metrics"]["accuracy"],
                  "recall_delta": metrics["recall"] - parent.metadata["test_metrics"]["recall"],
                  "note": metadata["evaluation_note"], "environment_changed": False}
    write_json(directory / "comparison.json", comparison)
    print(json.dumps(comparison, indent=2), flush=True)
    print("Candidate saved. Parent artifact and active configuration are unchanged.", flush=True)


if __name__ == "__main__":
    main()
