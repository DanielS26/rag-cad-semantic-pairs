"""Bounded smoke orchestration shared by fake tests and authorised live runs."""

import json
import platform
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from rag_cad.cad.representation import Encoding, JinaEncoder, build_features
from rag_cad.cad.scorer import CADScorer, synthetic_checkpoint
from rag_cad.cad.upstream_adapter import classifier, load_checkpoint, split_units
from rag_cad.operations.paths import local_path
from rag_cad.operations.provenance import digest, sha256, write_json
from rag_cad.operations.upstream import validate_resources
from rag_cad.rag.pipeline import Passage, RAGPipeline

QUERY = "Summarise the synthetic passage."
SENTENCES = ["Synthetic context.", "A synthetic target.", "Synthetic conclusion."]

# Fixed-vocabulary progress steps written to PROGRESS_PATH so a sanitized failure can be
# located without exposing command output, paths, or exception text.
STEPS = (
    "resources_validated", "segmenter_checked", "model_bundle_ready", "tokenizer_loaded",
    "model_loaded", "reference_checkpoint_loaded", "output_created", "features_encoded",
    "features_repeated", "determinism_checked", "reference_scored", "trained_saved",
    "reload_checked", "retrieval_checked", "rag_swap_checked", "report_written",
    "run_a_restored_read", "run_b_reload_checked", "run_b_compared",
)
PROGRESS_PATH: Path | None = None


def mark(step: str) -> None:
    if step not in STEPS:
        raise ValueError("Unknown progress step")
    if PROGRESS_PATH is None:
        return
    steps = json.loads(PROGRESS_PATH.read_text(encoding="utf-8")) if PROGRESS_PATH.exists() else []
    steps.append(step)
    PROGRESS_PATH.write_text(json.dumps(steps) + "\n", encoding="utf-8")


def resource_snapshot(directory: Path) -> dict:
    local_path(directory)
    disk = shutil.disk_usage(directory)
    if platform.system() == "Windows":
        import ctypes

        class MemoryStatus(ctypes.Structure):
            _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong),
                        *[(name, ctypes.c_ulonglong) for name in
                          ("total", "available", "page_total", "page_available",
                           "virtual_total", "virtual_available", "extended")]]

        memory = MemoryStatus()
        memory.length = ctypes.sizeof(memory)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):
            raise OSError("Cannot record Windows RAM")
        total, available = memory.total, memory.available
    else:
        fields = dict(line.split(":", 1) for line in Path("/proc/meminfo").read_text().splitlines())
        total = int(fields["MemTotal"].split()[0]) * 1024
        available = int(fields["MemAvailable"].split()[0]) * 1024
    return {"timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "ram_total_bytes": total, "ram_available_bytes": available,
            "disk_total_bytes": disk.total, "disk_used_bytes": disk.used,
            "disk_free_bytes": disk.free}


def runtime_identity() -> str:
    boot = Path("/proc/sys/kernel/random/boot_id")
    return digest({"hostname": platform.node(),
                   "boot_id": boot.read_text().strip() if boot.is_file() else "not-linux"})


class FakeBackend:
    kind = "fake"
    max_token_length = 0
    load_seconds = 0.0

    def encode(self, query, sentences):
        def encoder(text):
            self.max_token_length = max(self.max_token_length, len(text))
            values = np.array([ord(character) / 128 for character in text], dtype=np.float32)
            hidden = np.repeat(values[:, None], 1024, axis=1)
            hidden += values.mean() / 10
            return Encoding(hidden, np.ones(len(text)), [(index, index + 1) for index in range(len(text))])

        return build_features(query, sentences, encoder, "repo_compatible")

    def reference_score(self, features):
        positive = np.linspace(0.1, 0.9, len(features), dtype=np.float32)
        return np.column_stack([1 - positive, positive])

    def train_save(self, features, labels, path):
        write_json(path, {"fake_only": True, "scale": 0.25})
        return self.reload_score(features, path, sha256(path))

    def reload_score(self, features, path, expected_hash):
        if sha256(path) != expected_hash:
            raise ValueError("Fake checkpoint integrity failed")
        scale = json.loads(path.read_text(encoding="utf-8"))["scale"]
        positive = 1 / (1 + np.exp(-features[:, 0] * scale))
        return np.column_stack([1 - positive, positive])

    def retrieval_roundtrip(self, directory):
        vectors = np.eye(3, dtype=np.float32)
        np.save(directory / "fake-index.npy", vectors, allow_pickle=False)
        restored = np.load(directory / "fake-index.npy", allow_pickle=False)
        return int(np.argmax(restored @ vectors[1])), int(np.argmax(vectors @ vectors[1]))


class RealBackend:
    kind = "real"

    def __init__(self, profile: dict, source: Path, spec: dict, resources: Path, metadata: dict,
                 *, model_bundle: Path, allow_network: bool = False):
        for path in (source, resources, model_bundle):
            local_path(path)
        if profile.get("remote_code_approved") is not True:
            raise ValueError("Remote-code permission is unapproved")
        if allow_network and profile.get("network_approved") is not True:
            raise ValueError("Network permission is unapproved")
        started = time.perf_counter()
        import nltk

        validate_resources(profile, resources)
        mark("resources_validated")
        nltk.data.path[:] = [str(resources)]
        if split_units("\n".join(SENTENCES)) != SENTENCES:
            raise ValueError("Runtime segmenter changed canonical smoke units")
        mark("segmenter_checked")
        self.profile = profile
        self.metadata = metadata
        self.encoder = JinaEncoder(profile["expected"]["encoder_revision"],
                                   profile["expected"]["encoder_code_revision"], model_bundle,
                                   allow_network=allow_network, allow_remote_code=True, progress=mark)
        self.reference, self.reference_inspection = load_checkpoint(
            source / "classifier_fullcad.pt", spec["files"]["classifier_fullcad.pt"]["sha256"],
            with_inspection=True)
        mark("reference_checkpoint_loaded")
        self.load_seconds = time.perf_counter() - started

    @property
    def max_token_length(self):
        return self.encoder.max_token_length

    def encode(self, query, sentences):
        return build_features(query, sentences, self.encoder, self.profile["expected"]["representation"])

    def reference_score(self, features):
        import torch

        with torch.no_grad():
            return torch.softmax(self.reference(torch.from_numpy(features)), dim=-1).numpy()

    def train_save(self, features, labels, path):
        import torch

        torch.manual_seed(0)
        model = classifier()
        model.train()
        targets = torch.from_numpy(labels)
        weights = len(labels) / (2 * torch.bincount(targets, minlength=2).float())
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=1)
        optimizer.zero_grad()
        loss = torch.nn.functional.cross_entropy(model(torch.from_numpy(features)), targets,
                                                 weight=weights)
        loss.backward()
        optimizer.step()
        scheduler.step()
        model.eval()
        torch.save({"model_state_dict": model.state_dict(), "input_dim": 2048, "d_hid": 256,
                    "dropout": 0.3, "best_threshold": 0.5, "condition": "smoke_only", "seed": 0,
                    "representation_id": self.profile["expected"]["representation"],
                    "encoder_revision": self.profile["expected"]["encoder_revision"],
                    "encoder_code_revision": self.profile["expected"]["encoder_code_revision"],
                    "run_metadata": self.metadata}, path)
        with torch.no_grad():
            return torch.softmax(model(torch.from_numpy(features)), dim=-1).numpy()

    def reload_score(self, features, path, expected_hash):
        import torch

        model, self.trained_inspection = load_checkpoint(path, expected_hash, with_inspection=True)
        with torch.no_grad():
            return torch.softmax(model(torch.from_numpy(features)), dim=-1).numpy()

    def retrieval_roundtrip(self, directory):
        import faiss

        vectors = np.eye(3, dtype=np.float32)
        index = faiss.IndexFlatL2(3)
        index.add(vectors)
        before = int(index.search(vectors[1:2], 1)[1][0, 0])
        faiss.write_index(index, str(directory / "smoke.index"))
        restored = faiss.read_index(str(directory / "smoke.index"))
        after = int(restored.search(vectors[1:2], 1)[1][0, 0])
        return before, after


def check_probabilities(values: np.ndarray) -> None:
    if values.shape != (3, 2) or not np.isfinite(values).all():
        raise ValueError("Invalid smoke probability shape or values")
    if ((values < 0) | (values > 1)).any() or not np.allclose(values.sum(axis=1), 1):
        raise ValueError("Invalid two-class probabilities")


def smoke_a(backend, output: Path, metadata: dict, identity: str,
            *, atol: float, rtol: float, source_manifest: dict | None = None,
            validation_seconds: float = 0.0) -> dict:
    if not 0 <= atol <= 0.001 or not 0 <= rtol <= 0.001:
        raise ValueError("Explicit bounded determinism tolerances are required")
    local_path(output)
    if backend.kind == "real" and not source_manifest:
        raise ValueError("Real smoke requires retained release-validation evidence")
    output.mkdir(parents=True, exist_ok=False)
    mark("output_created")
    before = resource_snapshot(output)
    started = time.perf_counter()
    features = backend.encode(QUERY, SENTENCES)
    feature_seconds = time.perf_counter() - started
    mark("features_encoded")
    repeated = backend.encode(QUERY, SENTENCES)
    mark("features_repeated")
    if features.shape != (3, 2048) or features.dtype != np.float32 or not np.isfinite(features).all():
        raise ValueError("Smoke features must be finite float32 [3,2048]")
    np.testing.assert_allclose(features, repeated, atol=atol, rtol=rtol)
    mark("determinism_checked")
    reference = backend.reference_score(features)
    check_probabilities(reference)
    if np.ptp(reference[:, 1]) == 0:
        raise ValueError("Reference returned constant probabilities")
    mark("reference_scored")
    training_started = time.perf_counter()
    predictions = backend.train_save(features, np.array([0, 1, 0], dtype=np.int64), output / "model.pt")
    check_probabilities(predictions)
    checkpoint_hash = sha256(output / "model.pt")
    mark("trained_saved")
    restored = backend.reload_score(features, output / "model.pt", checkpoint_hash)
    np.testing.assert_allclose(predictions, restored, atol=atol, rtol=rtol)
    mark("reload_checked")
    training_seconds = time.perf_counter() - training_started
    retrieval_started = time.perf_counter()
    if backend.retrieval_roundtrip(output) != (1, 1):
        raise ValueError("Retrieval roundtrip changed expected chunk ID")
    mark("retrieval_checked")
    retrieval_seconds = time.perf_counter() - retrieval_started
    passages = [Passage("synthetic-chunk", tuple(SENTENCES))]
    pipeline = RAGPipeline(lambda query: passages, lambda prompt: prompt, "{query}\n{context}")
    no_defence = pipeline.run(QUERY)
    contract = {"representation_id": "synthetic-smoke-only", "encoder_revision": "a" * 40,
                "encoder_code_revision": "b" * 40}

    def swap_features(query, sentences):
        values = np.zeros((len(sentences), 2048), dtype=np.float32)
        values[:, 0] = [0, 1, 0]
        return values

    scorers = []
    for index in range(2):
        path = output / f"synthetic-scorer-{index}.npz"
        synthetic_checkpoint(path, inverted=bool(index), **contract)
        scorers.append(CADScorer(path, sha256(path), swap_features, synthetic_only=True, **contract))
    retained = pipeline.run(QUERY, scorers[0])
    removed = pipeline.run(QUERY, scorers[1])
    for key in ("retrieval_hash", "prompt_template_hash", "threshold"):
        if not no_defence[key] == retained[key] == removed[key]:
            raise ValueError("Checkpoint swap changed a fixed RAG component")
    if SENTENCES[1] in retained["answer"] or SENTENCES[0] in removed["answer"]:
        raise ValueError("Removed text reached the generator")
    mark("rag_swap_checked")
    np.save(output / "features.npy", features, allow_pickle=False)
    np.save(output / "predictions.npy", predictions, allow_pickle=False)
    source_manifest = source_manifest or {"synthetic_only": True, "files": []}
    write_json(output / "source_manifest.json", source_manifest)
    write_json(output / "preflight.json", metadata)
    if backend.kind == "real":
        write_json(output / "model_bundle_manifest.json", backend.encoder.bundle_manifest)
    after = resource_snapshot(output)
    report = {"execution_kind": backend.kind, "run": "A", "runtime_identity": identity,
              "metadata": metadata, "checkpoint_sha256": checkpoint_hash,
              "feature_shape": list(features.shape), "atol": atol, "rtol": rtol,
              "feature_seconds": feature_seconds,
              "timings_seconds": {"release_validation": validation_seconds,
                                  "backend_load": backend.load_seconds,
                                  "training_and_reload": training_seconds,
                                  "retrieval_roundtrip": retrieval_seconds},
              "maximum_token_length": backend.max_token_length,
              "token_measurement": "model_tokenizer" if backend.kind == "real" else "synthetic_characters",
              "resources_before": before, "resources_after": after,
              "source_manifest_sha256": sha256(output / "source_manifest.json"),
              "checkpoint_inspection": {"reference": getattr(backend, "reference_inspection", {"synthetic_only": True}),
                                        "trained": getattr(backend, "trained_inspection", {"synthetic_only": True}),
                                        "swap_heads": [scorer.inspection for scorer in scorers]},
              "smoke_rows_per_second": len(SENTENCES) / max(feature_seconds, 1e-9),
              "query": QUERY, "sentences": SENTENCES,
              "reference_probabilities": reference.tolist(),
              "reference_retained_ids": np.flatnonzero(reference[:, 1] <= 0.5).tolist(),
              "reference_removed_ids": np.flatnonzero(reference[:, 1] > 0.5).tolist(),
              "output_bytes_before_report": sum(path.stat().st_size for path in output.iterdir()),
              "rag": [no_defence, retained, removed], "duration_seconds": time.perf_counter() - started,
              "live_phase1b_passed": False}
    if backend.kind == "real":
        import torch

        report["peak_gpu_memory_bytes"] = torch.cuda.max_memory_allocated()
    write_json(output / "run_a.json", report)
    mark("report_written")
    return report


def smoke_b(backend, restored: Path, metadata: dict, identity: str) -> dict:
    local_path(restored)
    started = time.perf_counter()
    before = resource_snapshot(restored)
    original = json.loads((restored / "run_a.json").read_text(encoding="utf-8"))
    mark("run_a_restored_read")
    if original["runtime_identity"] == identity:
        raise ValueError("Run B requires a different fresh runtime")
    if original["execution_kind"] != backend.kind or original["metadata"] != metadata:
        raise ValueError("Run A and B execution/provenance mismatch")
    features = np.load(restored / "features.npy", allow_pickle=False)
    expected = np.load(restored / "predictions.npy", allow_pickle=False)
    actual = backend.reload_score(features, restored / "model.pt", original["checkpoint_sha256"])
    check_probabilities(actual)
    mark("run_b_reload_checked")
    np.testing.assert_allclose(actual, expected, atol=original["atol"], rtol=original["rtol"])
    mark("run_b_compared")
    return {"run": "B", "execution_kind": backend.kind, "runtime_identity": identity,
            "run_a_sha256": sha256(restored / "run_a.json"), "metadata": metadata,
            "restored_predictions_match": True, "profile_promotion_requires_review": True,
            "duration_seconds": time.perf_counter() - started,
            "resources_before": before, "resources_after": resource_snapshot(restored),
            "checkpoint_inspection": getattr(backend, "trained_inspection", {"synthetic_only": True}),
            "source_manifest_sha256": sha256(restored / "source_manifest.json")}