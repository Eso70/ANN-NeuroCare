import hashlib
import json
import math
from functools import lru_cache
from pathlib import Path

from app.ml.data import FEATURES, SUPPORTED_CONTRACTS, Preprocessor


class ModelUnavailable(Exception):
    pass


class Predictor:
    def __init__(self, directory: Path):
        metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
        if metadata["format_version"] not in (2, 3) or metadata.get("contract_id") not in SUPPORTED_CONTRACTS or metadata["features"] != list(FEATURES):
            raise ValueError("Unsupported model contract")
        self.threshold = metadata["threshold"]
        if isinstance(self.threshold, bool) or not isinstance(self.threshold, (int, float)) or not math.isfinite(self.threshold) or not 0 < self.threshold < 1:
            raise ValueError("Invalid decision threshold")
        self.version = metadata["version"]
        self.metadata = metadata
        if not isinstance(self.version, str) or not 1 <= len(self.version) <= 100:
            raise ValueError("Invalid model version")
        model_file = directory / "model.keras"
        if hashlib.sha256(model_file.read_bytes()).hexdigest() != metadata["model_sha256"]:
            raise ValueError("Model checksum mismatch")
        self.preprocessing = Preprocessor.from_dict(metadata["preprocessing"])
        import tensorflow as tf

        self.model = tf.keras.models.load_model(model_file, compile=False, safe_mode=True)
        if self.model.input_shape != (None, len(FEATURES)) or self.model.output_shape != (None, 1):
            raise ValueError("Invalid model dimensions")
        dense = [layer for layer in self.model.layers if isinstance(layer, tf.keras.layers.Dense)]
        self.architecture = {
            "hidden_units": [layer.units for layer in dense[:-1]],
            "dropout_rates": [float(layer.rate) for layer in self.model.layers if isinstance(layer, tf.keras.layers.Dropout)],
        }

    def predict(self, features: dict[str, float]) -> tuple[int, float, str]:
        import numpy as np

        values = [[features[name] for name in FEATURES]]
        transformed = np.asarray(self.preprocessing.transform(values), dtype="float32")
        probability = float(self.model(transformed, training=False).numpy()[0, 0])
        if not math.isfinite(probability) or not 0 <= probability <= 1:
            raise ModelUnavailable("Invalid model output")
        return int(probability >= self.threshold), probability, self.version


@lru_cache(maxsize=1)
def load_predictor(directory: Path | None) -> Predictor:
    if directory is None:
        raise ModelUnavailable("No model configured")
    if not directory.is_absolute():
        raise ModelUnavailable("MODEL_DIR must be absolute")
    try:
        return Predictor(directory)
    except Exception as exc:
        raise ModelUnavailable("Could not load configured model") from exc
