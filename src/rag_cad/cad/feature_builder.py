"""Project feature builder: records -> aligned CAD features, content-addressed shards, assembled sets."""

from pathlib import Path

import numpy as np

from rag_cad.cad.feature_store import (
    FEATURE_DIM,
    IDENTITY_FIELDS,
    ROW_FIELDS,
    read_feature_set,
    read_manifest,
    write_feature_set,
)
from rag_cad.cad.representation import RepresentationConfig
from rag_cad.data.conditions import CONDITIONS
from rag_cad.data.schema import SPLITS, record_content_hash, texts, validate_record
from rag_cad.data.split import apply_manifest, training_records
from rag_cad.operations.paths import local_path
from rag_cad.operations.provenance import digest, write_json

COMMON = "common"
COMMON_POOLS = {"validation": "common_validation", "test": "common_test"}


class FeatureBuilder:
    """One representation, one encoder, one environment identity for every row it produces."""

    def __init__(self, representation: RepresentationConfig, encode, *, feature_environment_id: str,
                 commit: str, config_sha256: str):
        self.representation = representation
        self.encode = encode
        self.identity = {"representation_id": representation.representation_id,
                         "encoder_revision": representation.encoder_revision,
                         "encoder_code_revision": representation.encoder_code_revision,
                         "segmenter": representation.segmenter,
                         "feature_environment_id": feature_environment_id, "commit": commit,
                         "config_sha256": config_sha256, "dtype": representation.dtype}
        if set(self.identity) != set(IDENTITY_FIELDS) or any(not value for value in self.identity.values()):
            raise ValueError("Feature identity fields are incomplete")

    def features(self, query: str, sentences: list[str]) -> np.ndarray:
        """The single implementation shared by training-time builds and runtime scoring."""
        return self.representation.build(query, sentences, self.encode)

    def claim_root(self, root: Path) -> Path:
        """One feature root holds one identity; a different builder is refused, never mixed in."""
        import json

        root = local_path(root)
        marker = root / "identity.json"
        if marker.exists():
            if json.loads(marker.read_text(encoding="utf-8")) != self.identity:
                raise ValueError("Feature root belongs to a different feature identity")
        else:
            root.mkdir(parents=True, exist_ok=True)
            write_json(marker, self.identity)
        return root

    def encode_record(self, record: dict, *, condition: str, start: int = 0, features: np.ndarray | None = None):
        """Rows for one record; features computed elsewhere from the same passes may be passed in."""
        record = validate_record(record, require_split=True)
        sentences = texts(record)
        if features is None:
            features = self.features(record["query"], sentences)
        if features.shape != (len(sentences), FEATURE_DIM):
            raise ValueError("Encoder returned a misaligned feature matrix")
        content = record_content_hash(record)
        rows, labels = [], []
        for offset, sentence in enumerate(record["sentences"]):
            values = {"feature_row_index": start + offset, "record_id": record["record_id"],
                      "group_id": record["group_id"], "family_id": record["family_id"],
                      "pair_member": record["pair_member"], "sentence_id": sentence["sentence_id"],
                      "is_target": sentence["is_target"], "label": sentence["label"],
                      "semantic_role": sentence["semantic_role"], "condition": condition,
                      "condition_source": record["condition_source"], "split": record["split"],
                      "record_content_hash": content,
                      "feature_environment_id": self.identity["feature_environment_id"],
                      "encoder_revision": self.identity["encoder_revision"],
                      "representation_id": self.identity["representation_id"]}
            rows.append({name: values[name] for name in ROW_FIELDS})
            labels.append(sentence["label"])
        return features, np.asarray(labels, dtype=np.int64), rows

    def build_rows(self, records, *, condition: str):
        blocks, labels, rows = [], [], []
        for record in records:
            features, record_labels, record_rows = self.encode_record(record, condition=condition, start=len(rows))
            blocks.append(features)
            labels.append(record_labels)
            rows.extend(record_rows)
        if not rows:
            raise ValueError("No records to encode")
        return np.concatenate(blocks), np.concatenate(labels), rows

    def shard_id(self, pool: str, records) -> str:
        return digest({"pool": pool, "identity": self.identity,
                       "records": [[record["record_id"], record_content_hash(record)] for record in records]})

    def build_pool(self, records, pool: str, root: Path, *, shard_records: int = 256,
                   resume: bool = False) -> list[dict]:
        """Encode a pool once as content-addressed shards; reuse only verified identical shards."""
        if type(shard_records) is not int or shard_records < 1:
            raise ValueError("Shard size must be a positive integer")
        root = self.claim_root(root)
        ordered = sorted((validate_record(record, require_split=True) for record in records),
                         key=lambda record: record["record_id"])
        if not ordered:
            raise ValueError(f"Pool has no records: {pool}")
        manifests = []
        for start in range(0, len(ordered), shard_records):
            chunk = ordered[start:start + shard_records]
            shard = self.shard_id(pool, chunk)
            directory = root / "shards" / pool / shard
            if directory.exists():
                if not resume:
                    raise FileExistsError("Shard already exists; pass resume to reuse verified shards")
                manifests.append(self._verified_reuse(directory, shard, chunk))
                continue
            features, labels, rows = self.build_rows(chunk, condition=pool)
            manifests.append(write_feature_set(directory, features, labels, rows, self.identity,
                                               kind="shard", name=shard))
        return manifests

    def _verified_reuse(self, directory: Path, shard: str, chunk) -> dict:
        _, _, _, manifest = read_feature_set(directory)
        expected = [[record["record_id"], record_content_hash(record)] for record in chunk]
        if manifest["identity"] != self.identity or manifest["ordered_record_hashes"] != expected \
                or manifest["name"] != shard or manifest["kind"] != "shard":
            raise ValueError("Existing shard identity or record hashes differ; refusing to reuse")
        return manifest

    def assemble(self, root: Path, condition: str, split: str, shard_manifests: list[dict]) -> dict:
        """Concatenate verified shards by stable row identity into assembled/<condition>/<split>."""
        root = self.claim_root(root)
        if split not in SPLITS:
            raise ValueError("Unknown split")
        collected = []
        parents = []
        for manifest in shard_manifests:
            if manifest["identity"] != self.identity:
                raise ValueError("Cannot assemble shards from a different feature identity")
            features, labels, rows, _ = read_feature_set(root / "shards" / manifest["pool"] / manifest["name"])
            for position, row in enumerate(rows):
                collected.append(((row["record_id"], row["sentence_id"]), features[position], labels[position], row))
            parents.append(manifest["name"])
        if not collected:
            raise ValueError("Nothing to assemble")
        collected.sort(key=lambda item: item[0])
        if len({key for key, *_ in collected}) != len(collected):
            raise ValueError("Duplicate row identities across shards")
        features = np.stack([item[1] for item in collected]).astype(np.float32)
        labels = np.asarray([item[2] for item in collected], dtype=np.int64)
        rows = []
        for index, (_, _, _, row) in enumerate(collected):
            if row["split"] != split:
                raise ValueError("Assembled rows must come from the requested split")
            rows.append({**row, "feature_row_index": index, "condition": condition})
        return write_feature_set(root / "assembled" / condition / split, features, labels, rows,
                                 self.identity, kind="assembled", name=f"{condition}/{split}",
                                 parents=parents)


def plan_pools(records, manifest: dict) -> dict[str, list[dict]]:
    """Training pools by condition_source and the common validation/test pools."""
    assigned = apply_manifest(records, manifest)
    pools = {}
    for source in ("base", "shared_malicious", "random_benign", "keyword_benign", "semantic_benign"):
        members = [record for record in assigned if record["split"] == "train"
                   and record["condition_source"] == source]
        if members:
            pools[source] = members
    for split, pool in COMMON_POOLS.items():
        members = [record for record in assigned if record["split"] == split]
        if members:
            pools[pool] = members
    return pools


def build_condition(builder: FeatureBuilder, records, manifest: dict, condition: str, split: str,
                    root: Path, *, shard_records: int = 256, resume: bool = False) -> dict:
    """Build the pools a condition/split needs (through the sanctioned selectors) and assemble them."""
    if split == "train":
        if condition not in CONDITIONS:
            raise ValueError("Unknown condition")
        selected = training_records(records, manifest, condition)
        pools = {}
        for record in selected:
            pools.setdefault(record["condition_source"], []).append(record)
        if set(pools) - set(CONDITIONS[condition]):
            raise ValueError("Training selection contains a source outside the condition")
    else:
        if condition != COMMON:
            raise ValueError("Validation and test sets are shared; build them as condition common")
        pool = COMMON_POOLS[split]
        members = plan_pools(records, manifest).get(pool, [])
        pools = {pool: members}
    shard_manifests = []
    for pool, members in sorted(pools.items()):
        for shard in builder.build_pool(members, pool, root, shard_records=shard_records, resume=resume):
            shard_manifests.append({**shard, "pool": pool})
    return builder.assemble(root, condition, split, shard_manifests)


def verify_condition(root: Path, condition: str, split: str) -> dict:
    """Re-read an assembled set and every parent shard, verifying hashes and identities."""
    root = local_path(root)
    _, _, rows, manifest = read_feature_set(root / "assembled" / condition / split)
    parents = {}
    for pool_directory in (root / "shards").iterdir() if (root / "shards").is_dir() else []:
        for shard_directory in pool_directory.iterdir():
            if shard_directory.name in manifest["parents"]:
                parents[shard_directory.name] = read_manifest(shard_directory)
    if set(parents) != set(manifest["parents"]):
        raise ValueError("Assembled set references shards that are missing")
    if any(parent["identity"] != manifest["identity"] for parent in parents.values()):
        raise ValueError("Parent shard identity differs from the assembled set")
    return {"condition": condition, "split": split, "rows": len(rows), "parents": sorted(parents),
            "identity": manifest["identity"], "counts": manifest["counts"]}
