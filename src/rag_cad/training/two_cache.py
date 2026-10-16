"""The two feature caches read side by side for the fold experiments (D-20261017-55 (b)).

The Phase 4 restored root holds the upstream D0 training rows (features/assembled/m0_base/train)
and the released CAD test rows (features/assembled/common/test) under one repo_compatible
identity; the Phase 6 family artefact holds the 800 family records per representation mode
(features/<mode>/shards/<pool>/... and features/<mode>/assembled/<condition>/train). Nothing is
re-encoded: the two caches are read only after their identities agree on representation_id,
encoder revision, encoder code revision, segmenter and dtype, exactly the fields features
check-families compares. Family rows are joined to the fold table by group_id, never family_id,
because the control records carry family_id null (docs/PHASE6_FEATURES_PLAN.md).
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from rag_cad.cad.feature_store import read_feature_set
from rag_cad.cad.representation import MODES
from rag_cad.data.conditions import CONDITIONS, PRIMARY
from rag_cad.data.folds import validate_folds
from rag_cad.data.schema import ContractError
from rag_cad.operations.paths import local_path

COMPARED_FIELDS = ("representation_id", "encoder_revision", "encoder_code_revision", "segmenter", "dtype")
INFORMATIONAL_FIELDS = ("commit", "config_sha256", "feature_environment_id")
FAMILY_POOLS = ("shared_malicious", "random_benign", "keyword_benign", "semantic_benign")
RECORD_KINDS = {"shared_malicious": "malicious", "semantic_benign": "twin",
                "random_benign": "random_control", "keyword_benign": "keyword_control"}
D0_SET = ("assembled", "m0_base", "train")
RELEASED_TEST_SET = ("assembled", "common", "test")


@dataclass
class FeatureSet:
    features: np.ndarray
    labels: np.ndarray
    rows: list[dict]
    manifest: dict

    def take(self, indices) -> "FeatureSet":
        indices = np.asarray(indices, dtype=np.int64)
        return FeatureSet(self.features[indices], self.labels[indices], [self.rows[i] for i in indices],
                          self.manifest)


@dataclass
class TwoCache:
    mode: str
    d0: FeatureSet
    released_test: FeatureSet
    pools: dict[str, FeatureSet]
    assembled: dict[str, FeatureSet]
    folds: dict[str, dict]  # keyed by group_id
    identity_check: dict
    summary: dict = field(default_factory=dict)

    @property
    def rounds(self) -> list[int]:
        return sorted({row["fold"] for row in self.folds.values()})


def phase4_feature_root(path: Path) -> Path:
    path = local_path(path)
    return path / "features" if (path / "features" / "identity.json").is_file() else path


def family_feature_root(path: Path, mode: str) -> Path:
    if mode not in MODES:
        raise ValueError(f"Unknown representation mode: {mode}")
    path = local_path(path)
    candidates = (path / "features" / mode, path / mode) + ((path,) if path.name == mode else ())
    for candidate in candidates:
        if (candidate / "identity.json").is_file() and (candidate / "shards").is_dir():
            return candidate
    raise ValueError(f"No {mode} feature root under the family artefact")


def _identity(root: Path) -> dict:
    marker = root / "identity.json"
    if not marker.is_file():
        raise ValueError(f"Feature root has no identity.json: {root}")
    return json.loads(marker.read_text(encoding="utf-8"))


def compare_identities(base: dict, family: dict) -> dict:
    """The check-families comparison applied to the two caches; informational fields only reported."""
    differences = {name: {"phase4": base.get(name), "family": family.get(name)}
                   for name in COMPARED_FIELDS if base.get(name) is None or base.get(name) != family.get(name)}
    return {"matches": not differences, "compared_fields": list(COMPARED_FIELDS), "differences": differences,
            "informational": {name: {"phase4": base.get(name), "family": family.get(name),
                                     "same": base.get(name) == family.get(name)}
                              for name in INFORMATIONAL_FIELDS},
            "message": "The two caches agree on representation, encoder, code, segmenter and dtype"
                       if not differences else
                       f"REFUSED: the two caches differ in {sorted(differences)}; no row was read for "
                       "training. Use caches of one representation or record a decision."}


def _read(root: Path, parts: tuple[str, ...], identity: dict) -> FeatureSet:
    features, labels, rows, manifest = read_feature_set(root.joinpath(*parts))
    if manifest["identity"] != identity:
        raise ValueError(f"{'/'.join(parts)} carries a different identity from its feature root")
    return FeatureSet(features, labels, rows, manifest)


def load_two_caches(phase4_root: Path, family_root: Path, mode: str, fold_rows: list[dict]) -> TwoCache:
    """Verify the identities, then load D0, the released test, every family pool and the assembled
    condition sets; join the family rows to the fold table by group_id. Refuses with a report
    (ContractError.report) when the identities differ."""
    base_root = phase4_feature_root(phase4_root)
    mode_root = family_feature_root(family_root, mode)
    base_identity, family_identity = _identity(base_root), _identity(mode_root)
    check = {"mode": mode, "phase4_root": str(base_root), "family_root": str(mode_root),
             **compare_identities(base_identity, family_identity)}
    if not check["matches"]:
        raise ContractError(check["message"], check)
    d0 = _read(base_root, D0_SET, base_identity)
    released = _read(base_root, RELEASED_TEST_SET, base_identity)
    if {row["condition_source"] for row in d0.rows} != set(CONDITIONS["m0_base"]):
        raise ValueError("D0 rows must all come from the base pool")
    pools = {}
    for pool in FAMILY_POOLS:
        directories = sorted((mode_root / "shards" / pool).iterdir()) if (mode_root / "shards" / pool).is_dir() else []
        if not directories:
            raise ValueError(f"Family pool {pool} has no shard")
        parts = [_read(mode_root, ("shards", pool, directory.name), family_identity) for directory in directories]
        rows = [row for part in parts for row in part.rows]
        if {row["condition_source"] for row in rows} != {pool}:
            raise ValueError(f"Shard rows of {pool} carry another condition source")
        pools[pool] = FeatureSet(np.concatenate([part.features for part in parts]),
                                 np.concatenate([part.labels for part in parts]), rows,
                                 {"shards": [part.manifest["name"] for part in parts]})
    assembled = {}
    for condition in PRIMARY:
        current = _read(mode_root, ("assembled", condition, "train"), family_identity)
        members = set(CONDITIONS[condition]) - {"base"}
        if {row["condition_source"] for row in current.rows} != members:
            raise ValueError(f"Assembled {condition} holds other sources than {sorted(members)}")
        expected = {(row["record_id"], row["sentence_id"]) for pool in members for row in pools[pool].rows}
        keys = [(row["record_id"], row["sentence_id"]) for row in current.rows]
        if len(keys) != len(set(keys)) or set(keys) != expected:
            raise ValueError(f"Assembled {condition} rows differ from the shards of its pools")
        assembled[condition] = current
    keyed = validate_folds(fold_rows)
    folds = {row["group_id"]: row for row in keyed.values()}
    family_groups = {row["group_id"] for pool in pools.values() for row in pool.rows}
    if family_groups != set(folds):
        raise ValueError("Fold table and family rows cover different groups (joined by group_id)")
    keys = {(row["record_id"], row["sentence_id"]) for row in d0.rows}
    if any((row["record_id"], row["sentence_id"]) in keys for pool in pools.values() for row in pool.rows):
        raise ValueError("A family row also occurs among the D0 rows")
    summary = {"mode": mode, "d0_rows": len(d0.rows), "released_test_rows": len(released.rows),
               "family_rows": {pool: len(value.rows) for pool, value in pools.items()},
               "assembled_rows": {condition: len(value.rows) for condition, value in assembled.items()},
               "groups": len(folds), "folds": sorted({row["fold"] for row in folds.values()}),
               "d0_row_digest": d0.manifest["row_digest"],
               "released_test_row_digest": released.manifest["row_digest"],
               "assembled_row_digests": {condition: value.manifest["row_digest"]
                                         for condition, value in assembled.items()},
               "identities": {"phase4": base_identity, "family": family_identity}}
    return TwoCache(mode, d0, released, pools, assembled, folds, check, summary)


def _fold(cache: TwoCache, row: dict) -> int:
    return cache.folds[row["group_id"]]["fold"]


def training_set(cache: TwoCache, condition: str, round_number: int | None) -> tuple[FeatureSet, dict]:
    """D0 alone for m0_base; D0 plus the round's training families of the condition's assembled set
    (the shared malicious additions and the condition's benign counterparts, CONDITIONS) otherwise."""
    if condition == "m0_base":
        if round_number is not None:
            raise ValueError("M0 has no family data and no round")
        return cache.d0, {"d0_rows": len(cache.d0.rows), "family_rows": 0, "training_families": 0}
    if condition not in PRIMARY:
        raise ValueError(f"Unknown training condition: {condition}")
    if round_number not in cache.rounds:
        raise ValueError("Round must name a fold of the table")
    family = cache.assembled[condition]
    chosen = [index for index, row in enumerate(family.rows) if _fold(cache, row) != round_number]
    part = family.take(chosen)
    held = {group for group, row in cache.folds.items() if row["fold"] == round_number}
    trained = {row["group_id"] for row in part.rows}
    if trained & held or trained != set(cache.folds) - held:
        raise ValueError("Training families do not reproduce the round's cut")
    sources = {row["condition_source"] for row in cache.d0.rows} | {row["condition_source"] for row in part.rows}
    if sources != set(CONDITIONS[condition]):
        raise ValueError("Training rows do not match the condition's sources")
    combined = FeatureSet(np.concatenate([cache.d0.features, part.features]),
                          np.concatenate([cache.d0.labels, part.labels]), cache.d0.rows + part.rows,
                          {"d0": cache.d0.manifest["row_digest"], "family": family.manifest["row_digest"]})
    return combined, {"d0_rows": len(cache.d0.rows), "family_rows": len(part.rows),
                      "training_families": len(trained),
                      "family_malicious_rows": int(part.labels.sum())}


def held_out_set(cache: TwoCache, round_number: int | None) -> FeatureSet:
    """All four record kinds of the round's held-out families (every family when round is None)."""
    features, labels, rows = [], [], []
    for pool in FAMILY_POOLS:
        current = cache.pools[pool]
        chosen = [index for index, row in enumerate(current.rows)
                  if round_number is None or _fold(cache, row) == round_number]
        part = current.take(chosen)
        features.append(part.features)
        labels.append(part.labels)
        rows.extend(part.rows)
    if not rows:
        raise ValueError("Held-out set is empty")
    return FeatureSet(np.concatenate(features), np.concatenate(labels), rows, {"round": round_number})
