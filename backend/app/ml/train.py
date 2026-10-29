"""Offline training CLI. Never called by API routes."""
import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.ml.data import CONTRACT_ID, FEATURES, TARGET_DESCRIPTION, Preprocessor, read_dataset, split_indices
from app.ml.evaluation import binary_metrics, select_validation_threshold


def main() -> None:
    parser = argparse.ArgumentParser(description="Train an educational binary ANN from a local CSV")
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--source", required=True, help="Dataset provenance/license and population notes")
    parser.add_argument("--output", type=Path, default=Path("../artifacts"))
    parser.add_argument("--epochs", type=int, default=30)
    args = parser.parse_args()
    if not 1 <= args.epochs <= 1000:
        parser.error("epochs must be between 1 and 1000")
    manifest = args.csv.with_suffix(".json")
    if manifest.is_file() and json.loads(manifest.read_text(encoding="utf-8")).get("contract_id", CONTRACT_ID) != CONTRACT_ID:
        parser.error("This CLI uses the 2015 contract; use app.ml.train_2021 for the converted 2021 survey")
    rows, labels = read_dataset(args.csv)
    os.environ.setdefault("TF_DETERMINISTIC_OPS", "1")
    import numpy as np
    import sklearn
    import tensorflow as tf
    from sklearn.linear_model import LogisticRegression

    seed = 42
    tf.keras.utils.set_random_seed(seed)
    train_indices, val_indices, test_indices = split_indices(rows, labels, seed)
    x_train = [rows[i] for i in train_indices]
    x_val = [rows[i] for i in val_indices]
    x_test = [rows[i] for i in test_indices]
    y_train = [labels[i] for i in train_indices]
    y_val = [labels[i] for i in val_indices]
    y_test = [labels[i] for i in test_indices]
    preprocessing = Preprocessor.fit(x_train)
    train = np.asarray(preprocessing.transform(x_train), dtype="float32")
    validation = np.asarray(preprocessing.transform(x_val), dtype="float32")
    test = np.asarray(preprocessing.transform(x_test), dtype="float32")
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(len(FEATURES),)),
        tf.keras.layers.Dense(32, activation="relu"),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(16, activation="relu"),
        tf.keras.layers.Dense(1, activation="sigmoid"),
    ])
    model.compile(optimizer="adam", loss="binary_crossentropy")
    history = model.fit(
        train, np.asarray(y_train, dtype="float32"),
        validation_data=(validation, np.asarray(y_val, dtype="float32")),
        epochs=args.epochs, batch_size=512, verbose=2,
        callbacks=[tf.keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=5, restore_best_weights=True
        )],
    )
    validation_scores = model.predict(validation, verbose=0).reshape(-1)
    threshold = select_validation_threshold(y_val, validation_scores)
    baseline = LogisticRegression(max_iter=500, random_state=seed).fit(train, y_train)
    baseline_threshold = select_validation_threshold(y_val, baseline.predict_proba(validation)[:, 1])
    # Both cutoffs are frozen using validation data before test evaluation.
    probabilities = model.predict(test, verbose=0).reshape(-1)
    metrics = binary_metrics(y_test, probabilities, threshold)
    baseline_metrics = {"logistic_regression": binary_metrics(y_test, baseline.predict_proba(test)[:, 1], baseline_threshold),
                        "logistic_regression_threshold": baseline_threshold,
                        "majority_class_accuracy": max(y_test.count(0), y_test.count(1)) / len(y_test)}
    version = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    directory = args.output.resolve() / version
    directory.mkdir(parents=True, exist_ok=False)
    model.save(directory / "model.keras")
    np.savez_compressed(directory / "split_indices.npz", train=train_indices,
                        validation=val_indices, test=test_indices)
    metadata = {
        "format_version": 3, "contract_id": CONTRACT_ID, "target": TARGET_DESCRIPTION, "version": version, "features": list(FEATURES),
        "threshold": threshold,
        "threshold_selection": {"split": "validation", "objective": "maximum F2", "beta": 2,
                                "test_used_for_selection": False},
        "validation_metrics": binary_metrics(y_val, validation_scores, threshold), "source": args.source, "seed": seed,
        "dataset_sha256": hashlib.sha256(args.csv.read_bytes()).hexdigest(),
        "model_sha256": hashlib.sha256((directory / "model.keras").read_bytes()).hexdigest(),
        "split_sizes": {"train": len(x_train), "validation": len(x_val), "test": len(x_test)},
        "epochs_completed": len(history.history["loss"]),
        "preprocessing": preprocessing.to_dict(), "test_metrics": metrics,
        "baseline_metrics": baseline_metrics,
        "split_method": "5 stratified group folds by identical features: train 3, validation 1, test 1",
        "class_weighting": "none; natural class distribution preserved",
        "class_counts": {"0": labels.count(0), "1": labels.count(1)},
        "unique_profiles": len({tuple(row) for row in rows}),
        "dependencies": {"tensorflow": tf.__version__, "numpy": np.__version__, "sklearn": sklearn.__version__},
        "limitations": "Educational dataset classifier; not clinically validated or calibrated for individual risk.",
    }
    # Write manifest last: incomplete runs cannot be loaded by the API.
    (directory / "metadata.json").write_text(json.dumps(metadata, indent=2, allow_nan=False), encoding="utf-8")
    print(f"Saved model and measured test metrics to {directory}")
    print("Review the evaluation before setting MODEL_DIR. No model is auto-promoted.")


if __name__ == "__main__":
    main()
