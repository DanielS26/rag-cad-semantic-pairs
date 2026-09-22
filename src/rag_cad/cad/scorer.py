"""Checkpoint-backed sentence scorer; synthetic NPZ heads are smoke-only."""

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from rag_cad.cad.upstream_adapter import STATE_SHAPES, split_units, validate_checkpoint
from rag_cad.operations.paths import local_path
from rag_cad.operations.provenance import sha256

THRESHOLD = 0.5


@dataclass(frozen=True)
class ScoredPassage:
    """Handoff Section 7.5: ordered sentences, probabilities, decisions, retained/removed text, latency."""

    query: str
    passage: str
    sentences: tuple[str, ...]
    probabilities: tuple[float, ...]
    decisions: tuple[bool, ...]
    retained_ids: tuple[int, ...]
    retained_text: str
    removed_ids: tuple[int, ...]
    removed_text: str
    threshold: float
    checkpoint_id: str
    representation_id: str
    segmentation_seconds: float
    scoring_seconds: float

    def as_dict(self) -> dict:
        return asdict(self)


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
                 synthetic_only: bool = False, threshold: float = THRESHOLD):
        local_path(checkpoint_path)
        if sha256(checkpoint_path) != expected_hash:
            raise ValueError("Scorer checkpoint hash mismatch")
        if threshold != THRESHOLD:
            raise ValueError("The primary threshold is fixed at 0.5 by the experimental contract")
        self.checkpoint_id = expected_hash
        self.feature_builder = feature_builder
        self.representation_id = representation_id
        self.threshold = threshold
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

    @classmethod
    def from_representation(cls, checkpoint_path: Path, expected_hash: str, representation, encode, *,
                            synthetic_only: bool = False, threshold: float = THRESHOLD) -> "CADScorer":
        """Bind the scorer to the same RepresentationConfig implementation the feature builder uses."""
        return cls(checkpoint_path, expected_hash,
                   lambda query, sentences: representation.build(query, sentences, encode),
                   representation_id=representation.representation_id,
                   encoder_revision=representation.encoder_revision,
                   encoder_code_revision=representation.encoder_code_revision,
                   synthetic_only=synthetic_only, threshold=threshold)

    def score_passage(self, query: str, passage: str, *, tokenize=None) -> ScoredPassage:
        """Segment with the frozen segmenter, score every sentence, split retained from removed text."""
        started = time.perf_counter()
        sentences = split_units(passage, tokenize) if passage.strip() else []
        segmentation_seconds = time.perf_counter() - started
        started = time.perf_counter()
        probabilities = self(query, sentences) if sentences else np.zeros(0, dtype=np.float32)
        scoring_seconds = time.perf_counter() - started
        decisions = tuple(bool(value > self.threshold) for value in probabilities)
        retained = tuple(index for index, removed in enumerate(decisions) if not removed)
        removed = tuple(index for index, flagged in enumerate(decisions) if flagged)
        return ScoredPassage(query=query, passage=passage, sentences=tuple(sentences),
                             probabilities=tuple(float(value) for value in probabilities),
                             decisions=decisions, retained_ids=retained,
                             retained_text="\n".join(sentences[index] for index in retained),
                             removed_ids=removed, removed_text="\n".join(sentences[index] for index in removed),
                             threshold=self.threshold, checkpoint_id=self.checkpoint_id,
                             representation_id=self.representation_id,
                             segmentation_seconds=segmentation_seconds, scoring_seconds=scoring_seconds)

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