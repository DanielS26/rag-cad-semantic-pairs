"""A torch-free stand-in for the trainer: deterministic, instant, without scientific meaning.

It writes the same kind of checkpoint record, hash and metadata as the real trainer so the
Phase 4 plumbing can be exercised in CPU environments that have no torch installed.
"""

import json
from pathlib import Path

import numpy as np

from rag_cad.operations.provenance import sha256, write_json
from rag_cad.training.recipe import class_weights


class FakeTrainer:
    kind = "fake"
    checkpoint_file = "model.json"

    def __init__(self, recipe: dict):
        self.recipe = recipe

    def fit(self, features, labels, *, seed: int) -> dict:
        """A class-mean direction classifier; the seed scales the logits so seeds differ visibly."""
        values = np.asarray(features, dtype=np.float64)
        targets = np.asarray(labels, dtype=np.int64)
        weights = class_weights(targets)
        direction = values[targets == 1].mean(axis=0) - values[targets == 0].mean(axis=0)
        norm = float(np.linalg.norm(direction))
        if norm > 0:
            direction = direction / norm
        midpoint = float(((values[targets == 1].mean(axis=0) + values[targets == 0].mean(axis=0)) / 2) @ direction)
        model = {"direction": [float(value) for value in direction], "bias": -midpoint,
                 "scale": 1.0 + 0.1 * seed, "seed": seed}
        history = {"epoch_mean_loss": [round(1.0 / (epoch + 1), 6) for epoch in range(self.recipe["epochs"])],
                   "class_weights": weights, "rows": int(len(targets)), "positives": int(targets.sum()),
                   "device": "fake"}
        return {"model": model, "seed": seed, "history": history}

    @staticmethod
    def _probabilities(model: dict, features) -> np.ndarray:
        logits = (np.asarray(features, dtype=np.float64) @ np.asarray(model["direction"]) + model["bias"]) * model["scale"]
        positive = 1.0 / (1.0 + np.exp(-logits))
        return np.column_stack([1 - positive, positive]).astype(np.float32)

    def predict(self, trained: dict, features) -> np.ndarray:
        return self._probabilities(trained["model"], features)

    def save(self, trained: dict, path: Path, metadata: dict) -> str:
        write_json(path, {"fake_only": True, "model": trained["model"], **metadata})
        return sha256(path)

    def reload_predict(self, path: Path, expected_hash: str, features) -> np.ndarray:
        if sha256(path) != expected_hash:
            raise ValueError("Checkpoint hash mismatch before deserialization")
        checkpoint = json.loads(path.read_text(encoding="utf-8"))
        if checkpoint.get("fake_only") is not True:
            raise ValueError("Not a fake checkpoint")
        return self._probabilities(checkpoint["model"], features)
