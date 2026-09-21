"""Lazy segmenter and checkpoint primitives matching pinned CAD source."""

import re
from pathlib import Path

import numpy as np

from rag_cad.operations.paths import local_path
from rag_cad.operations.provenance import sha256

STATE_SHAPES = {
    "net.0.weight": (256, 2048), "net.0.bias": (256,),
    "net.3.weight": (128, 256), "net.3.bias": (128,),
    "net.6.weight": (2, 128), "net.6.bias": (2,),
}


def split_units(text: str, tokenize=None) -> list[str]:
    if tokenize is None:
        from nltk.tokenize import sent_tokenize

        tokenize = sent_tokenize
    return [sentence.strip() for block in re.split(r"\n+", text.replace("\\n", "\n"))
            if block.strip() for sentence in tokenize(block.strip()) if sentence.strip()]


def validate_checkpoint(checkpoint: dict) -> dict:
    for field, expected in {"input_dim": 2048, "d_hid": 256, "dropout": 0.3,
                            "best_threshold": 0.5}.items():
        if checkpoint.get(field) != expected:
            raise ValueError(f"Incompatible checkpoint metadata: {field}")
    state = checkpoint.get("model_state_dict", {})
    if set(state) != set(STATE_SHAPES):
        raise ValueError("Checkpoint state keys mismatch")
    tensors = {}
    for name, shape in STATE_SHAPES.items():
        values = np.asarray(state[name])
        if values.shape != shape or values.dtype != np.float32 or not np.isfinite(values).all():
            raise ValueError("Checkpoint tensor shape/dtype/finite check failed")
        tensors[name] = {"shape": list(shape), "dtype": str(values.dtype), "finite": True,
                         "min": float(values.min()), "max": float(values.max()),
                         "nonconstant": bool(np.ptp(values) > 0)}
    return {"metadata": {name: checkpoint[name] for name in
                         ("input_dim", "d_hid", "dropout", "best_threshold")},
            "tensors": tensors, "parameter_count": sum(int(np.prod(shape)) for shape in STATE_SHAPES.values())}


def classifier():
    from torch import nn

    class Head(nn.Module):
        def __init__(self):
            super().__init__()
            self.net = nn.Sequential(nn.Linear(2048, 256), nn.ReLU(), nn.Dropout(0.3),
                                     nn.Linear(256, 128), nn.ReLU(), nn.Dropout(0.3),
                                     nn.Linear(128, 2))

        def forward(self, features):
            return self.net(features)

    return Head()


def load_checkpoint(path: Path, expected_hash: str, *, with_inspection: bool = False):
    local_path(path)
    if sha256(path) != expected_hash:
        raise ValueError("Checkpoint hash mismatch before deserialization")
    import torch

    checkpoint = torch.load(path, map_location="cpu", weights_only=True)
    inspection = validate_checkpoint(checkpoint)
    inspection.update(sha256=expected_hash, weights_only=True, map_location="cpu")
    model = classifier()
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    model.eval()
    return (model, inspection) if with_inspection else model