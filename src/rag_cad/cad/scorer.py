"""Checkpoint-backed sentence scorer; synthetic NPZ heads are smoke-only."""

import json
from pathlib import Path

import numpy as np

from rag_cad.cad.upstream_adapter import STATE_SHAPES, validate_checkpoint
from rag_cad.operations.paths import local_path
from rag_cad.operations.provenance import sha256


def synthetic_checkpoint(path: Path, *, inverted: bool, representation_id: str,
                         encoder_revision: str, encoder_code_revision: str) -> None:
    local_path(path)
    state = {name: np.zeros(shape, dtype=np.float32) for name, shape in STATE_SHAPES.items()}
    state["net.0.weight"][0, 0] = 1
    state["net.3.weight"][0, 0] = 1
    state["net.6.weight"][1, 0] = -4 if inverted else 4
    state["net.6.bias"][1] = 2 if inverted else -2
    metadata = {"format": "synthetic-smoke-v1", "input_dim": 2048, "d_hid": 256,
                "dropout": 0.3, "best_threshold": 0.5, "representation_id": representation_id,
                "encoder_revision": encoder_revision, "encoder_code_revision": encoder_code_revision}
    with path.open("xb") as handle:
        np.savez_compressed(handle, metadata=json.dumps(metadata), **state)


class CADScorer:
    def __init__(self, checkpoint_path: Path, expected_hash: str, feature_builder, *,
                 representation_id: str, encoder_revision: str, encoder_code_revision: str,
                 synthetic_only: bool = False):
        local_path(checkpoint_path)
        if sha256(checkpoint_path) != expected_hash:
            raise ValueError("Scorer checkpoint hash mismatch")
        self.checkpoint_id = expected_hash
        self.feature_builder = feature_builder
        if synthetic_only:
            with np.load(checkpoint_path, allow_pickle=False) as archive:
                metadata = json.loads(str(archive["metadata"]))
                if metadata.get("format") != "synthetic-smoke-v1":
                    raise ValueError("Expected explicit synthetic smoke checkpoint")
                if set(archive.files) != set(STATE_SHAPES) | {"metadata"}:
                    raise ValueError("Synthetic checkpoint fields mismatch")
                self.state = {name: archive[name].copy() for name in STATE_SHAPES}
        else:
            import torch

            metadata = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
            self.state = metadata["model_state_dict"]
        for key, expected in {"representation_id": representation_id,
                              "encoder_revision": encoder_revision,
                              "encoder_code_revision": encoder_code_revision}.items():
            if metadata.get(key) != expected:
                raise ValueError(f"Scorer runtime/checkpoint mismatch: {key}")
        self.inspection = validate_checkpoint(metadata | {"model_state_dict": self.state})
        self.synthetic_only = synthetic_only
        self.model = None
        if not synthetic_only:
            from rag_cad.cad.upstream_adapter import classifier

            self.model = classifier()
            self.model.load_state_dict(self.state, strict=True)
            self.model.eval()

    def __call__(self, query: str, sentences: list[str]) -> np.ndarray:
        features = np.asarray(self.feature_builder(query, sentences))
        if features.shape != (len(sentences), 2048) or features.dtype != np.float32 or not np.isfinite(features).all():
            raise ValueError("Scorer expects aligned finite float32 features")
        if self.synthetic_only:
            hidden = np.maximum(features @ self.state["net.0.weight"].T + self.state["net.0.bias"], 0)
            hidden = np.maximum(hidden @ self.state["net.3.weight"].T + self.state["net.3.bias"], 0)
            logits = hidden @ self.state["net.6.weight"].T + self.state["net.6.bias"]
            exponentials = np.exp(logits - logits.max(axis=1, keepdims=True))
            return (exponentials / exponentials.sum(axis=1, keepdims=True))[:, 1]
        import torch

        with torch.no_grad():
            return torch.softmax(self.model(torch.from_numpy(features)), dim=-1)[:, 1].numpy()