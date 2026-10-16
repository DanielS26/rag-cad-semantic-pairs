"""Phase 6 family feature stage and its readiness check (docs/PHASE6_FEATURES_PLAN.md).

The stage encodes exactly the family records of the pending list, in both representation modes
from one set of encoder passes, into a new feature root per mode beside (never over) any restored
cache. Before the encoder is loaded it compares its repo_compatible identity with the values the
Phase 4 run recorded and stops when an encoder, code, segmenter, dtype or representation hash
differs. The readiness check runs on CPU after the run: every pending record once in each mode,
the records unchanged, and the rows joined to the fold table by group_id (never family_id).
"""

import json
import os
import time
from dataclasses import replace
from pathlib import Path

import numpy as np

from rag_cad.cad.feature_builder import FeatureBuilder
from rag_cad.cad.feature_store import read_feature_set, write_feature_set
from rag_cad.cad.representation import MODES, RepresentationConfig, build_mode_features
from rag_cad.config import load_config
from rag_cad.data.conditions import CONDITIONS
from rag_cad.data.folds import validate_folds
from rag_cad.data.jsonl import load_records, read_jsonl
from rag_cad.data.schema import record_content_hash, texts
from rag_cad.data.split import apply_manifest
from rag_cad.operations.paths import local_path
from rag_cad.operations.provenance import digest, sha256, write_json

STAGE = "phase6_family_features"
FAMILY_POOLS = ("shared_malicious", "random_benign", "keyword_benign", "semantic_benign")
FAMILY_CONDITIONS = ("m1_random", "m2_keyword", "m3_semantic")
REPORT = "family_features_report.json"
IDENTITY_CHECK = "identity_check.json"
BUNDLE_MANIFEST = "bundle_manifest.json"
INFORMATIONAL_FIELDS = ("commit", "config_sha256", "feature_environment_id")


def read_pending(path: Path) -> list[str]:
    """The pending list: record ids, sorted, one per line, no repeats."""
    ids = [line.strip() for line in local_path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    if not ids or len(set(ids)) != len(ids) or ids != sorted(ids):
        raise ValueError("Pending list must hold sorted, unique record ids")
    return ids


def select_family_records(records, manifest: dict, pending: list[str], *, groups: int = 0) -> list[dict]:
    """Exactly the pending records, all in train under the all-train manifest; groups > 0 keeps the
    first groups by group_id (synthetic or pilot runs only, recorded in the report)."""
    if isinstance(groups, bool) or type(groups) is not int or groups < 0:
        raise ValueError("Groups must be a non-negative integer (0 means every group)")
    assigned = apply_manifest(records, manifest)
    if {record["record_id"] for record in assigned} != set(pending):
        raise ValueError("Input records differ from the pending list")
    if any(record["split"] != "train" for record in assigned):
        raise ValueError("The family feature build reads the all-train manifest (data split --all-train)")
    if any(record["condition_source"] not in FAMILY_POOLS for record in assigned):
        raise ValueError("Pending records must be family records")
    if groups:
        kept = set(sorted({record["group_id"] for record in assigned})[:groups])
        assigned = [record for record in assigned if record["group_id"] in kept]
    return sorted(assigned, key=lambda record: record["record_id"])


def mode_representations(base: RepresentationConfig) -> dict[str, RepresentationConfig]:
    """Both modes over one encoder, code and segmenter: they share every pass."""
    return {mode: replace(base, mode=mode) for mode in MODES}


def load_reference(path: Path) -> dict:
    reference = json.loads(local_path(path).read_text(encoding="utf-8"))
    if set(reference.get("compared_fields", ())) - set(reference.get("identity", {})) \
            or not reference.get("compared_fields"):
        raise ValueError("Reference identity must name compared fields it holds")
    return reference


def check_reference(identity: dict, reference: dict) -> dict:
    """Compare the repo_compatible identity with the recorded Phase 4 values."""
    recorded = reference["identity"]
    differences = {field: {"phase4": recorded[field], "this_run": identity[field]}
                   for field in reference["compared_fields"] if identity[field] != recorded[field]}
    return {"matches": not differences, "reference": reference.get("source_artefact"),
            "compared_fields": list(reference["compared_fields"]), "differences": differences,
            "informational": {field: {"phase4": recorded.get(field), "this_run": identity[field],
                                      "same": recorded.get(field) == identity[field]}
                              for field in INFORMATIONAL_FIELDS},
            "message": "Encoder, code, segmenter, dtype and representation hashes match the Phase 4 "
                       "features" if not differences else
                       "STOP: the encoder identity differs from the Phase 4 recorded values in "
                       f"{sorted(differences)}; no record was encoded. Resolve the profile or record a "
                       "decision before any rerun."}


class CountingEncoder:
    """Counts encoder passes so the report can show one set of passes served both modes."""

    def __init__(self, encode):
        self.encode = encode
        self.passes = 0

    def __call__(self, text: str):
        self.passes += 1
        return self.encode(text)


def build_family_features(representations: dict[str, RepresentationConfig], encode, records, output: Path, *,
                          feature_environment_id: str, commit: str, config_sha256: str,
                          shard_records: int = 256) -> dict:
    """Shards per pool and assembled m1/m2/m3 train sets, one feature root per mode, one set of passes."""
    if set(representations) != set(MODES):
        raise ValueError("Both representation modes are required")
    shared = {(rep.encoder_revision, rep.encoder_code_revision, rep.segmenter, rep.dtype, rep.attention)
              for rep in representations.values()}
    if len(shared) != 1:
        raise ValueError("Both modes must share one encoder, code, segmenter and dtype")
    if type(shard_records) is not int or shard_records < 1:
        raise ValueError("Shard size must be a positive integer")
    counting = CountingEncoder(encode)
    builders = {mode: FeatureBuilder(rep, counting, feature_environment_id=feature_environment_id,
                                     commit=commit, config_sha256=config_sha256)
                for mode, rep in representations.items()}
    roots = {}
    for mode, builder in builders.items():
        root = local_path(output / "features" / mode)
        if root.exists():
            raise FileExistsError("Feature root already exists; the family stage writes a new root")
        roots[mode] = builder.claim_root(root)
    pools = {}
    for record in sorted(records, key=lambda record: record["record_id"]):
        pools.setdefault(record["condition_source"], []).append(record)
    shards = {mode: {} for mode in MODES}
    started = time.perf_counter()
    for pool, members in sorted(pools.items()):
        for start in range(0, len(members), shard_records):
            chunk = members[start:start + shard_records]
            collected = {mode: ([], [], []) for mode in MODES}
            for record in chunk:
                computed = build_mode_features(record["query"], texts(record), counting)
                for mode, builder in builders.items():
                    blocks, labels, rows = collected[mode]
                    features, record_labels, record_rows = builder.encode_record(
                        record, condition=pool, start=len(rows), features=computed[mode])
                    blocks.append(features)
                    labels.append(record_labels)
                    rows.extend(record_rows)
            for mode, builder in builders.items():
                blocks, labels, rows = collected[mode]
                name = builder.shard_id(pool, chunk)
                manifest = write_feature_set(roots[mode] / "shards" / pool / name, np.concatenate(blocks),
                                             np.concatenate(labels), rows, builder.identity,
                                             kind="shard", name=name)
                shards[mode].setdefault(pool, []).append({**manifest, "pool": pool})
    encode_seconds = time.perf_counter() - started
    assembled = {mode: {} for mode in MODES}
    for mode, builder in builders.items():
        for condition in FAMILY_CONDITIONS:
            parts = [manifest for pool in CONDITIONS[condition] for manifest in shards[mode].get(pool, [])]
            if parts:
                assembled[mode][condition] = builder.assemble(roots[mode], condition, "train", parts)
    sentences = sum(len(record["sentences"]) for record in records)
    expected = len(records) + 2 * sentences
    if counting.passes != expected:
        raise ValueError("Encoder pass count differs from one pass per record and two per sentence")
    summary = ("name", "counts", "row_digest", "parents")
    return {"records": len(records), "sentences": sentences,
            "groups": len({record["group_id"] for record in records}),
            "encoder_passes": counting.passes, "expected_passes_one_set": expected,
            "encode_seconds": encode_seconds,
            "seconds_per_pass": encode_seconds / counting.passes if counting.passes else None,
            "modes": {mode: {"identity": builders[mode].identity,
                             "shards": {pool: [{key: item[key] for key in ("name", "counts", "row_digest")}
                                               for item in items] for pool, items in shards[mode].items()},
                             "assembled": {condition: {key: value[key] for key in summary}
                                           for condition, value in assembled[mode].items()}}
                       for mode in MODES}}


def _inputs(args):
    experiment = load_config(args.experiment)
    records, inventory = load_records(args.input)
    manifest = json.loads(local_path(args.split_manifest).read_text(encoding="utf-8"))
    pending = read_pending(args.pending)
    selected = select_family_records(records, manifest, pending, groups=args.groups)
    return experiment, inventory, selected, {"split_manifest_sha256": sha256(args.split_manifest),
                                             "pending_sha256": sha256(args.pending),
                                             "pending_records": len(pending), "groups_limit": args.groups}


def _stage(kind: str, args, representations, encode, *, feature_environment_id: str, commit: str,
           experiment: dict, inventory: dict, selected: list[dict], provenance: dict, identity_check,
           mark=lambda step: None, extra: dict | None = None) -> dict:
    output = args.output
    started = time.perf_counter()
    result = build_family_features(representations, encode, selected, output,
                                   feature_environment_id=feature_environment_id, commit=commit,
                                   config_sha256=digest(experiment), shard_records=args.shard_records)
    mark("family_features_built")
    report = {"execution_kind": kind, "stage": STAGE, "input": inventory, **provenance,
              "identity_check": identity_check, **result, **(extra or {}),
              "stage_seconds": time.perf_counter() - started}
    write_json(output / REPORT, report)
    mark("family_report_written")
    return report


def _prepare_output(output: Path) -> Path:
    output = local_path(output)
    if output.exists():
        raise FileExistsError("Stage output already exists; the family stage writes a new directory")
    output.mkdir(parents=True)
    return output


def _checked(output: Path, identity: dict, reference_path: Path | None):
    if reference_path is None:
        return None
    check = check_reference(identity, load_reference(reference_path))
    write_json(output / IDENTITY_CHECK, check)
    if not check["matches"]:
        raise ValueError(check["message"])
    return check


def fake_build_families(args) -> dict:
    """CPU plumbing with the synthetic encoder; no scientific meaning."""
    from rag_cad.cad.fake_encoder import FAKE_REPRESENTATION, FakeEncoder

    experiment, inventory, selected, provenance = _inputs(args)
    output = _prepare_output(args.output)
    representations = mode_representations(FAKE_REPRESENTATION)
    builder_identity = FeatureBuilder(representations["repo_compatible"], None, feature_environment_id="fake-local",
                                      commit="fake-local", config_sha256=digest(experiment)).identity
    check = _checked(output, builder_identity, args.reference)
    encoder = FakeEncoder()
    return _stage("fake", args, representations, encoder, feature_environment_id="fake-local",
                  commit="fake-local", experiment=experiment, inventory=inventory, selected=selected,
                  provenance=provenance, identity_check=check,
                  extra={"maximum_token_length": encoder.max_token_length})


def build_families(args, profile: dict, evidence: dict) -> dict:
    """The real stage behind the features gate: identity check first, then the encoder."""
    from rag_cad.operations.phase4 import prepare_environment

    prepare_environment()  # same cuBLAS workspace setting as the Phase 4 m0 process, before torch loads
    from rag_cad.cad.representation import JinaEncoder
    from rag_cad.operations import smoke
    from rag_cad.operations.upstream import prepare_resources, validate_resources

    experiment, inventory, selected, provenance = _inputs(args)
    mode = experiment.get("representation")
    if mode is None:
        raise ValueError("Primary representation is unresolved (D-20260921-05)")
    if mode != profile["expected"]["representation"]:
        raise ValueError("Experiment representation differs from the tested profile; rerun the gate in that mode")
    for path in (args.resources, args.model_bundle):
        local_path(path, args.workspace)
    smoke.PROGRESS_PATH = local_path(args.workspace) / "smoke_progress.json"
    smoke.PROGRESS_PATH.unlink(missing_ok=True)
    output = _prepare_output(args.output)
    representations = mode_representations(RepresentationConfig.from_profile(profile, mode=mode))
    identity = FeatureBuilder(representations["repo_compatible"], None,
                              feature_environment_id=evidence["environment_id"], commit=args.commit,
                              config_sha256=digest(experiment)).identity
    check = _checked(output, identity, args.reference)
    smoke.mark("family_identity_checked")
    if not args.resources.exists():
        prepare_resources(profile, args.resources, allow_network=args.allow_network)
    validate_resources(profile, args.resources)
    smoke.mark("resources_validated")
    import nltk

    nltk.data.path[:] = [str(args.resources)]
    base = representations["repo_compatible"]
    encoder = JinaEncoder(base.encoder_revision, base.encoder_code_revision, args.model_bundle,
                          allow_network=args.allow_network, allow_remote_code=True, progress=smoke.mark)
    write_json(output / BUNDLE_MANIFEST, encoder.bundle_manifest)
    return _stage("real", args, representations, encoder, feature_environment_id=evidence["environment_id"],
                  commit=args.commit, experiment=experiment, inventory=inventory, selected=selected,
                  provenance=provenance, identity_check=check, mark=smoke.mark,
                  extra={"preflight": evidence,
                         "cublas_workspace_config": os.environ.get("CUBLAS_WORKSPACE_CONFIG"), "bundle_manifest_sha256": sha256(output / BUNDLE_MANIFEST),
                         "bundle_files": encoder.bundle_manifest["files"],
                         "maximum_token_length": encoder.max_token_length})


def _feature_root(path: Path) -> Path:
    path = local_path(path)
    return path / "features" if (path / "features").is_dir() else path


def check_family_features(features: Path, records, pending: list[str], fold_rows, reference: dict | None) -> dict:
    """Readiness after the run: coverage once per mode, unchanged records, the fold join by group_id."""
    root = _feature_root(features)
    by_id = {record["record_id"]: record for record in records}
    if set(pending) - set(by_id):
        raise ValueError("Pending records are missing from the input")
    folds = validate_folds(fold_rows)
    fold_of_group = {row["group_id"]: row["fold"] for row in folds.values()}
    pending_groups = {by_id[record_id]["group_id"] for record_id in pending}
    if pending_groups != set(fold_of_group):
        raise ValueError("Fold table and pending records cover different groups")
    errors, modes, row_keys = [], {}, {}
    for mode in MODES:
        mode_root = root / mode
        if not (mode_root / "identity.json").is_file():
            errors.append(f"{mode}: feature root missing")
            continue
        identity = json.loads((mode_root / "identity.json").read_text(encoding="utf-8"))
        seen, rows_all, pools, pool_keys, pool_shards = {}, [], {}, {}, {}
        for pool_dir in sorted((mode_root / "shards").iterdir()) if (mode_root / "shards").is_dir() else []:
            for shard_dir in sorted(pool_dir.iterdir()):
                try:
                    _, _, rows, manifest = read_feature_set(shard_dir)
                except (ValueError, OSError, KeyError) as error:
                    errors.append(f"{mode}: shards/{pool_dir.name}/{shard_dir.name} unreadable "
                                  f"({type(error).__name__}: {error})")
                    continue
                if manifest["identity"] != identity:
                    errors.append(f"{mode}: shard {shard_dir.name} has a different identity")
                pools[pool_dir.name] = pools.get(pool_dir.name, 0) + manifest["counts"]["records"]
                pool_keys.setdefault(pool_dir.name, set()).update(
                    (row["record_id"], row["sentence_id"]) for row in rows)
                pool_shards.setdefault(pool_dir.name, set()).add(manifest["name"])
                for record_id, content in manifest["ordered_record_hashes"]:
                    seen[record_id] = seen.get(record_id, 0) + 1
                    if record_id in by_id and record_content_hash(by_id[record_id]) != content:
                        errors.append(f"{mode}: {record_id} changed since it was encoded")
                rows_all.extend(rows)
        missing = sorted(set(pending) - set(seen))
        extra = sorted(set(seen) - set(pending))
        repeated = sorted(record_id for record_id, count in seen.items() if count > 1)
        if missing or extra or repeated:
            errors.append(f"{mode}: coverage missing {len(missing)}, extra {len(extra)}, repeated {len(repeated)}")
        expected_rows = sum(len(by_id[record_id]["sentences"]) for record_id in pending)
        if len(rows_all) != expected_rows:
            errors.append(f"{mode}: {len(rows_all)} rows, expected {expected_rows}")
        row_keys[mode] = sorted((row["record_id"], row["sentence_id"], row["label"], row["group_id"])
                                for row in rows_all)
        assembled = {}
        for condition in FAMILY_CONDITIONS:
            try:
                _, _, rows, manifest = read_feature_set(mode_root / "assembled" / condition / "train")
            except (ValueError, OSError, KeyError) as error:
                errors.append(f"{mode}: assembled/{condition}/train unreadable ({type(error).__name__}: {error})")
                continue
            members = [pool for pool in CONDITIONS[condition] if pool != "base"]
            expected_keys = set().union(*(pool_keys.get(pool, set()) for pool in members))
            assembled_keys = [(row["record_id"], row["sentence_id"]) for row in rows]
            if len(assembled_keys) != len(set(assembled_keys)) or set(assembled_keys) != expected_keys:
                errors.append(f"{mode}: {condition} rows ({len(assembled_keys)}) differ from its pools' "
                              f"shard rows ({len(expected_keys)})")
            if manifest["identity"] != identity:
                errors.append(f"{mode}: {condition} has a different identity from the feature root")
            expected_parents = set().union(*(pool_shards.get(pool, set()) for pool in members))
            if sorted(manifest["parents"]) != sorted(expected_parents):
                errors.append(f"{mode}: {condition} parents differ from the shards of its pools")
            sources = {row["condition_source"] for row in rows}
            if sources != set(CONDITIONS[condition]) - {"base"}:
                errors.append(f"{mode}: {condition} holds sources {sorted(sources)}")
            unjoined = sorted({row["group_id"] for row in rows} - set(fold_of_group))
            if unjoined:
                errors.append(f"{mode}: {condition} rows with group_id outside the fold table")
            rounds = {}
            for round_number in sorted(set(fold_of_group.values())):
                train = [row for row in rows if fold_of_group.get(row["group_id"]) != round_number]
                held = [row for row in rows if fold_of_group.get(row["group_id"]) == round_number]
                train_groups = {row["group_id"] for row in train}
                held_groups = {row["group_id"] for row in held}
                expected_train = {group for group, fold in fold_of_group.items() if fold != round_number}
                expected_held = {group for group, fold in fold_of_group.items() if fold == round_number}
                if train_groups != expected_train or held_groups != expected_held:
                    errors.append(f"{mode}: {condition} round {round_number} does not reproduce the fold split")
                rounds[str(round_number)] = {"training_families": len(train_groups),
                                             "held_out_families": len(held_groups),
                                             "training_rows": len(train), "held_out_rows": len(held)}
            assembled[condition] = {"rows": len(rows), "records": len({row["record_id"] for row in rows}),
                                    "rows_with_null_family_id": sum(row["family_id"] is None for row in rows),
                                    "rounds": rounds}
        modes[mode] = {"identity": identity, "records": len(seen), "rows": len(rows_all),
                       "records_per_pool": pools, "assembled": assembled}
    if len(row_keys) == len(MODES) and len({tuple(keys) for keys in row_keys.values()}) != 1:
        errors.append("The two modes hold different rows")
    identities = [modes[mode]["identity"] for mode in MODES if mode in modes]
    if len(identities) == len(MODES):
        if identities[0]["representation_id"] == identities[1]["representation_id"]:
            errors.append("The two modes share one representation_id")
        if any(identities[0][field] != identities[1][field]
               for field in ("encoder_revision", "encoder_code_revision", "segmenter", "dtype", "commit")):
            errors.append("The two modes come from different encoders or commits")
    identity_check = None
    if reference is not None and "repo_compatible" in modes:
        identity_check = check_reference(modes["repo_compatible"]["identity"], reference)
        if not identity_check["matches"]:
            errors.append("repo_compatible identity differs from the Phase 4 recorded values")
    return {"features": str(root), "pending_records": len(pending), "groups": len(pending_groups),
            "folds": len(set(fold_of_group.values())), "join_field": "group_id", "modes": modes,
            "identity_check": identity_check, "errors": errors, "ready": not errors}


def check_families_command(args) -> dict:
    from rag_cad.data.schema import ContractError

    local_path(args.output)
    records, inventory = load_records(args.input)
    reference = None if args.skip_reference else load_reference(args.reference)
    report = check_family_features(args.features, records, read_pending(args.pending),
                                   read_jsonl(local_path(args.folds)), reference)
    report = {"input": inventory, "pending_sha256": sha256(args.pending), "folds_sha256": sha256(args.folds),
              **report}
    write_json(args.output, report)
    if not report["ready"]:
        raise ContractError("Family features are not ready", report)
    return report
