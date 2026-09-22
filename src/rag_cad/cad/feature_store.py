"""Content-addressed feature sets: aligned tensors, row metadata and a hashed manifest (handoff 7.2)."""

from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from rag_cad.data.jsonl import read_jsonl, write_jsonl
from rag_cad.operations.paths import local_path
from rag_cad.operations.provenance import digest, sha256, write_json

FEATURE_DIM = 2048
MANIFEST_SCHEMA = "rag_cad.feature_set/1"
ROW_FIELDS = ("feature_row_index", "record_id", "group_id", "family_id", "pair_member", "sentence_id",
              "is_target", "label", "semantic_role", "condition", "condition_source", "split",
              "record_content_hash", "feature_environment_id", "encoder_revision", "representation_id")
IDENTITY_FIELDS = ("representation_id", "encoder_revision", "encoder_code_revision", "segmenter",
                   "feature_environment_id", "commit", "config_sha256", "dtype")
FILES = ("features.npz", "rows.jsonl")


def check_alignment(features: np.ndarray, labels: np.ndarray, rows: list[dict]) -> None:
    """The builder contract: len(X) == len(y) == number of metadata rows, field for field."""
    if not isinstance(features, np.ndarray) or features.ndim != 2 or features.shape[1] != FEATURE_DIM:
        raise ValueError("Features must be a two-dimensional array with 2048 columns")
    if features.dtype != np.float32 or not np.isfinite(features).all():
        raise ValueError("Features must be finite float32")
    if not isinstance(labels, np.ndarray) or labels.dtype != np.int64 or labels.shape != (len(features),):
        raise ValueError("Labels must be int64 with one entry per feature row")
    if len(rows) != len(features):
        raise ValueError("Feature rows and metadata rows are misaligned")
    for position, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != set(ROW_FIELDS):
            raise ValueError("Metadata row fields must be exactly the contract fields")
        if row["feature_row_index"] != position:
            raise ValueError("feature_row_index must be sequential from zero")
        if row["label"] not in (0, 1) or int(labels[position]) != row["label"]:
            raise ValueError("Label tensor and metadata labels disagree")


def row_digest(rows: list[dict]) -> str:
    return digest([[row["record_id"], row["sentence_id"], row["record_content_hash"], row["label"]]
                   for row in rows])


def counts(rows: list[dict]) -> dict:
    return {"rows": len(rows), "records": len({row["record_id"] for row in rows}),
            "malicious_rows": sum(row["label"] for row in rows),
            "benign_rows": sum(1 - row["label"] for row in rows),
            "target_rows": sum(1 for row in rows if row["is_target"]),
            "families": len({row["family_id"] for row in rows if row["family_id"] is not None}),
            "groups": len({row["group_id"] for row in rows})}


def write_feature_set(directory: Path, features: np.ndarray, labels: np.ndarray, rows: list[dict],
                      identity: dict, *, kind: str, name: str, parents: list[str] = ()) -> dict:
    """Write features.npz, rows.jsonl and manifest.json into a new directory; never overwrite."""
    directory = local_path(directory)
    if set(identity) != set(IDENTITY_FIELDS) or any(not value for value in identity.values()):
        raise ValueError("Feature identity fields are incomplete")
    check_alignment(features, labels, rows)
    for row in rows:
        if (row["representation_id"], row["encoder_revision"], row["feature_environment_id"]) != (
                identity["representation_id"], identity["encoder_revision"], identity["feature_environment_id"]):
            raise ValueError("Metadata rows carry a different identity from the feature set")
    directory.mkdir(parents=True, exist_ok=False)
    with (directory / "features.npz").open("xb") as handle:
        np.savez_compressed(handle, X=features, y=labels)
    write_jsonl(directory / "rows.jsonl", rows)
    manifest = {"schema": MANIFEST_SCHEMA, "kind": kind, "name": name, "identity": dict(identity),
                "parents": list(parents), "counts": counts(rows), "row_digest": row_digest(rows),
                "ordered_record_hashes": _ordered_record_hashes(rows),
                "files": {file: sha256(directory / file) for file in FILES},
                "created_utc": datetime.now(timezone.utc).isoformat()}
    write_json(directory / "manifest.json", manifest)
    return manifest


def _ordered_record_hashes(rows: list[dict]) -> list[list[str]]:
    ordered, seen = [], set()
    for row in rows:
        if row["record_id"] not in seen:
            seen.add(row["record_id"])
            ordered.append([row["record_id"], row["record_content_hash"]])
    return ordered


def read_manifest(directory: Path) -> dict:
    import json

    manifest = json.loads((local_path(directory) / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema") != MANIFEST_SCHEMA:
        raise ValueError("Unknown feature set manifest")
    return manifest


def read_feature_set(directory: Path) -> tuple[np.ndarray, np.ndarray, list[dict], dict]:
    """Load a feature set only after every file hash and the row alignment verify."""
    directory = local_path(directory)
    manifest = read_manifest(directory)
    for file in FILES:
        if sha256(directory / file) != manifest["files"][file]:
            raise ValueError(f"Feature set file hash mismatch: {file}")
    with np.load(directory / "features.npz", allow_pickle=False) as archive:
        if set(archive.files) != {"X", "y"}:
            raise ValueError("Feature archive must hold exactly X and y")
        features, labels = archive["X"], archive["y"]
    rows = read_jsonl(directory / "rows.jsonl")
    if any(not isinstance(row, dict) or set(row) != set(ROW_FIELDS) for row in rows):
        raise ValueError("Metadata row fields must be exactly the contract fields")
    rows = [{name: row[name] for name in ROW_FIELDS} for row in rows]
    check_alignment(features, labels, rows)
    if row_digest(rows) != manifest["row_digest"] or counts(rows) != manifest["counts"]:
        raise ValueError("Feature set rows differ from the manifest")
    return features, labels, rows, manifest
