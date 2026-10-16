"""Phase 1A command surface; real execution requires explicit reviewed inputs."""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from rag_cad.config import load_config
from rag_cad.data import commands as data_commands
from rag_cad.data.conditions import PRIMARY
from rag_cad.evaluation.bow_baseline import bow_baseline_command
from rag_cad.evaluation.posthoc import leak_excluded_report
from rag_cad.operations import artefacts, family_features
from rag_cad.operations import features as feature_operations
from rag_cad.operations import phase4 as phase4_operations
from rag_cad.operations import smoke as smoke_operations
from rag_cad.operations.paths import execution_paths, local_path
from rag_cad.operations.preflight import PreflightError, preflight
from rag_cad.operations.provenance import canonical_json, sha256, verify_upstream, write_json
from rag_cad.operations.released_test import ARCHIVE, evaluate_released_test
from rag_cad.operations.smoke import FakeBackend, RealBackend, runtime_identity, smoke_a, smoke_b
from rag_cad.operations.upstream import fetch_release, prepare_resources, validate_release

FAILURE_RECORD = "last_failure.json"
PROGRESS_RECORD = "smoke_progress.json"


def execution_options(parser):
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="rag-cad")
    root.add_argument("--repo", type=Path, default=Path.cwd())
    commands = root.add_subparsers(dest="command", required=True)
    audit = commands.add_parser("audit").add_subparsers(dest="action", required=True)
    audit.add_parser("upstream")
    environment = commands.add_parser("environment").add_subparsers(dest="action", required=True)
    check = environment.add_parser("preflight")
    execution_options(check)
    check.add_argument("--stage", choices=["smoke", "conformance", "features", "train", "evaluate"], required=True)
    check.add_argument("--output", type=Path, required=True)
    upstream = commands.add_parser("upstream").add_subparsers(dest="action", required=True)
    for name in ("fetch-cad", "validate-cad"):
        command = upstream.add_parser(name)
        execution_options(command)
        command.add_argument("--release", type=Path, default=Path("configs/upstream/cad_release.yaml"))
        command.add_argument("--source", "--destination", dest="source", type=Path, required=True)
        command.add_argument("--output", type=Path, required=True)
        command.add_argument("--allow-network", action="store_true")
    artefact = commands.add_parser("artefact").add_subparsers(dest="action", required=True)
    publish = artefact.add_parser("publish")
    publish.add_argument("--source", type=Path, required=True)
    publish.add_argument("--storage-config", type=Path, required=True)
    publish.add_argument("--stage", required=True)
    publish.add_argument("--run-id", required=True)
    publish.add_argument("--metadata", type=Path, required=True)
    for name in ("verify", "restore"):
        command = artefact.add_parser(name)
        command.add_argument("--manifest", type=Path, required=True)
        if name == "restore":
            command.add_argument("--destination", type=Path, required=True)
            command.add_argument("--receipt", type=Path)
    data = commands.add_parser("data").add_subparsers(dest="action", required=True)
    adapt = data.add_parser("adapt-cad")
    adapt.add_argument("--release", type=Path, default=Path("configs/upstream/cad_release.yaml"))
    adapt.add_argument("--source", type=Path, required=True)
    adapt.add_argument("--output", type=Path, required=True)
    adapt.add_argument("--skip-paraphrased", action="store_true")
    check = data.add_parser("selfcheck")
    check.add_argument("--batch", type=Path, required=True)
    check.add_argument("--manifest", type=Path, required=True)
    check.add_argument("--previous", type=Path, action="append", default=[])
    check.add_argument("--prompt", type=Path)
    check.add_argument("--semantic", type=Path)
    check.add_argument("--report", type=Path, required=True)
    check.add_argument("--stage", choices=["drafting", "review"], default="drafting")
    check.add_argument("--strict", action="store_true")
    screen = data.add_parser("prescreen")
    screen.add_argument("--input", type=Path, required=True)
    screen.add_argument("--families", type=Path, required=True)
    screen.add_argument("--output", type=Path, required=True)
    screen.add_argument("--experiment", type=Path, default=Path("configs/experiment.yaml"))
    screen.add_argument("--minimum-per-role", type=int, default=4)
    for name in ("validate", "split", "check-leakage", "compare-budgets"):
        command = data.add_parser(name)
        command.add_argument("--input", type=Path, required=True)
        command.add_argument("--output", type=Path, required=True)
        command.add_argument("--experiment", type=Path, default=Path("configs/experiment.yaml"))
        if name == "compare-budgets":
            command.add_argument("--manifest", type=Path, required=True)
        if name == "check-leakage":
            source = command.add_mutually_exclusive_group(required=True)
            source.add_argument("--manifest", type=Path, help="split manifest from data split")
            source.add_argument("--folds", type=Path,
                                help="fold table from data assign-folds; checks the cut of --round")
            command.add_argument("--round", type=int,
                                 help="with --folds: the held-out fold of the round (1 to 5)")
        if name == "compare-budgets":
            command.add_argument("--conditions", nargs="+", default=list(PRIMARY))
        if name == "split":
            command.add_argument(
                "--all-train", action="store_true",
                help="put every group in train with no validation or test partition (the manifest "
                     "the family feature build reads, D-20261013-28); ignores split_ratios and the "
                     "seed, refuses records pinned to test")
        if name == "validate":
            command.add_argument("--roundtrip", action="store_true")
            command.add_argument("--profile", type=Path)
            command.add_argument("--resources", type=Path)
    folds = data.add_parser(
        "assign-folds", help="five-fold family assignment (D-20261013-28, D-20261017-51)",
        description="Assign every family (all records of its group) to one of five folds with the "
                    "experiment's split_seed, five families per semantic role per fold and, within "
                    "role, attack category (malicious record source: bipia_adapted task_type, "
                    "asb_adapted operational) balanced to at most one apart. Writes the fold table "
                    "to --output (JSONL: family_id, group_id, fold, semantic_role, attack_category, "
                    "cue_position) and the achieved counts to its sibling <stem>.summary.json; "
                    "refuses to overwrite either.")
    folds.add_argument("--input", type=Path, required=True, help="family batch file or directory")
    folds.add_argument("--manifest", type=Path, required=True, help="family_manifest.jsonl")
    folds.add_argument("--output", type=Path, required=True, help="fold table, e.g. folds_v1.jsonl")
    folds.add_argument("--experiment", type=Path, default=Path("configs/experiment.yaml"))
    features = commands.add_parser("features").add_subparsers(dest="action", required=True)
    for name in ("fake-build", "build"):
        command = features.add_parser(name)
        command.add_argument("--condition", required=True)
        command.add_argument("--split", choices=["train", "validation", "test"], required=True)
        command.add_argument("--input", type=Path, required=True)
        command.add_argument("--manifest", type=Path, required=True)
        command.add_argument("--output", type=Path, required=True)
        command.add_argument("--experiment", type=Path, default=Path("configs/experiment.yaml"))
        command.add_argument("--shard-records", type=int, default=256)
        command.add_argument("--resume", action="store_true")
        if name == "build":
            execution_options(command)
            command.add_argument("--resources", type=Path, required=True)
            command.add_argument("--model-bundle", type=Path, required=True)
            command.add_argument("--allow-network", action="store_true")
    pending = Path("datasets/raw/augmentation/review/encoder_pending_v1.txt")
    reference = Path("configs/phase6/phase4_feature_identity.json")
    for name in ("fake-build-families", "build-families"):
        real = name == "build-families"
        command = features.add_parser(
            name, help=("gated family feature stage (Phase 6)" if real else
                        "CPU twin of build-families with the synthetic encoder"),
            description="Encode exactly the records of --pending (the 800 family records) in both "
                        "representation modes from one set of encoder passes. Writes a new stage "
                        "directory --output holding features/<mode>/ (identity.json, shards/<pool>/, "
                        "assembled/m1_random|m2_keyword|m3_semantic/train/), "
                        "family_features_report.json and identity_check.json; refuses an existing "
                        "--output, so it never writes over a restored cache. "
                        + ("Behind the features gate (tested profile, approved budget); compares the "
                           "repo_compatible identity with --reference before loading the encoder and "
                           "stops when any compared hash differs; records the model bundle manifest."
                           if real else "Synthetic identity and encoder; no scientific meaning. "
                           "--reference is optional here."))
        command.add_argument("--input", type=Path, required=True, help="family batch directory")
        command.add_argument("--split-manifest", type=Path, required=True,
                             help="all-train split manifest (data split --all-train); not a Drive "
                                  "artefact manifest")
        command.add_argument("--pending", type=Path, default=pending)
        command.add_argument("--output", type=Path, required=True)
        command.add_argument("--experiment", type=Path, default=Path("configs/experiment.yaml"))
        command.add_argument("--shard-records", type=int, default=256)
        command.add_argument("--groups", type=int, default=0,
                             help="encode only the first N groups by group_id (0, the default, means all)")
        command.add_argument("--reference", type=Path, default=reference if real else None,
                             help="Phase 4 feature identity to compare with")
        if real:
            execution_options(command)
            command.add_argument("--resources", type=Path, required=True)
            command.add_argument("--model-bundle", type=Path, required=True)
            command.add_argument("--allow-network", action="store_true")
    ready = features.add_parser(
        "check-families", help="readiness of the family features for the fold experiments (CPU)",
        description="Verify a family feature directory after the encoder run: every record of --pending "
                    "in exactly one shard per mode, both modes present with the same rows, records "
                    "unchanged since encoding, the repo_compatible identity equal to --reference, and "
                    "every assembled set joined to --folds by group_id reproducing each round's "
                    "training and held-out families. Writes --output; exits 2 when not ready.")
    ready.add_argument("--features", type=Path, required=True, help="stage directory or its features/")
    ready.add_argument("--input", type=Path, required=True, help="family batch directory")
    ready.add_argument("--pending", type=Path, default=pending)
    ready.add_argument("--folds", type=Path, default=Path("datasets/raw/augmentation/folds_v1.jsonl"))
    ready.add_argument("--reference", type=Path, default=reference)
    ready.add_argument("--skip-reference", action="store_true",
                       help="do not compare with --reference (synthetic features only)")
    ready.add_argument("--output", type=Path, required=True)
    m0 = commands.add_parser("m0").add_subparsers(dest="action", required=True)
    for name in ("fake-run", "run"):
        command = m0.add_parser(name)
        command.add_argument("--release", type=Path, default=Path("configs/upstream/cad_release.yaml"))
        command.add_argument("--source", type=Path, required=True)
        command.add_argument("--output", type=Path, required=True)
        command.add_argument("--experiment", type=Path, default=Path("configs/experiment.yaml"))
        if name == "fake-run":
            command.add_argument("--seeds", type=int, nargs="*")
        else:
            execution_options(command)
            command.add_argument("--resources", type=Path, required=True)
            command.add_argument("--model-bundle", type=Path, required=True)
            command.add_argument("--allow-network", action="store_true")
    evaluation = commands.add_parser("evaluation").add_subparsers(dest="action", required=True)
    leak = evaluation.add_parser("leak-excluded")
    leak.add_argument("--artefact", type=Path, required=True)
    leak.add_argument("--output", type=Path, required=True)
    leak.add_argument("--experiment", type=Path, default=Path("configs/experiment.yaml"))
    bow = evaluation.add_parser(
        "bow-baseline", help="bag-of-words baseline on the family folds (D-20261016-49 (d))",
        description="Train the audit's multinomial naive Bayes (unigrams and bigrams of the query and "
                    "non-target sentences, add-one smoothing) on each round's training families and "
                    "score the held-out twin and malicious records. Writes overall, per-fold, per-role, "
                    "per-category and per-cue figures with the within-family paired share to --output, "
                    "prints the result as JSON and a table to standard error. CPU only.")
    bow.add_argument("--input", type=Path, required=True, help="family batch file or directory")
    bow.add_argument("--manifest", type=Path, required=True, help="family_manifest.jsonl")
    bow.add_argument("--folds", type=Path, required=True, help="fold table from data assign-folds")
    bow.add_argument("--output", type=Path, required=True)
    conformance = commands.add_parser("conformance").add_subparsers(dest="action", required=True)
    fake_test = conformance.add_parser("fake-released-test")
    fake_test.add_argument("--archive", type=Path, required=True)
    fake_test.add_argument("--output", type=Path, required=True)
    fake_test.add_argument("--records", type=int, default=0)
    released = conformance.add_parser("released-test")
    execution_options(released)
    released.add_argument("--release", type=Path, default=Path("configs/upstream/cad_release.yaml"))
    released.add_argument("--source", type=Path, required=True)
    released.add_argument("--resources", type=Path, required=True)
    released.add_argument("--model-bundle", type=Path, required=True)
    released.add_argument("--output", type=Path, required=True)
    released.add_argument("--allow-network", action="store_true")
    released.add_argument("--records", type=int, default=0)
    released.add_argument("--domains", nargs="*", default=[])
    smoke = commands.add_parser("smoke").add_subparsers(dest="action", required=True)
    fake = smoke.add_parser("fake")
    fake.add_argument("--output", type=Path, required=True)
    for name in ("run-a", "run-b"):
        command = smoke.add_parser(name)
        execution_options(command)
        command.add_argument("--release", type=Path, default=Path("configs/upstream/cad_release.yaml"))
        command.add_argument("--source", type=Path, required=True)
        command.add_argument("--resources", type=Path, required=True)
        command.add_argument("--model-bundle", type=Path, required=True)
        command.add_argument("--output", type=Path, required=True)
        command.add_argument("--allow-network", action="store_true")
        if name == "run-b":
            command.add_argument("--destination", type=Path, required=True)
            command.add_argument("--receipt", type=Path, required=True)
    return root


def _gate(args):
    if not args.execute:
        raise ValueError("Real commands require --execute and a separately approved profile")
    execution_paths(args)
    profile = load_config(args.profile)
    if profile.get("compute_budget_approved") is not True:
        raise ValueError("Real execution requires a separately approved bounded compute budget")
    if getattr(args, "allow_network", False) and profile.get("network_approved") is not True:
        raise ValueError("Downloads require reviewed profile permission as well as --allow-network")
    if args.command in ("smoke", "conformance"):
        if profile.get("remote_code_approved") is not True:
            raise ValueError("Remote-code execution requires explicit profile approval")
        tolerance = profile.get("tolerance", {})
        if any(type(tolerance.get(key)) not in (float, int) or not 0 <= tolerance[key] <= 0.001
               for key in ("atol", "rtol")):
            raise ValueError("Explicit bounded smoke tolerances are required")
    stage = {"environment": getattr(args, "stage", None), "features": "features",
             "conformance": "conformance", "m0": "train"}.get(args.command, "smoke")
    evidence = preflight(args.repo, args.commit, profile, stage, args.lock, args.workspace)
    return profile, evidence


def execute(args) -> dict:
    if args.command == "audit":
        return verify_upstream(args.repo)
    if args.command == "data":
        return data_commands.run(args)
    if args.command == "artefact":
        if args.action == "verify":
            return artefacts.verify(args.manifest)
        if args.action == "restore":
            local_path(args.destination)
            if args.receipt:
                local_path(args.receipt)
                if args.receipt.resolve().is_relative_to(args.destination.resolve()):
                    raise ValueError("Receipt must be outside restored payload")
            restored = artefacts.restore(args.manifest, args.destination)
            if args.receipt:
                write_json(args.receipt, {"manifest": restored,
                           "source_manifest_sha256": sha256(args.manifest),
                           "destination": str(args.destination.resolve())})
            return restored
        local_path(args.source)
        local_path(args.metadata)
        config = load_config(args.storage_config)
        if not config.get("artefact_root"):
            raise ValueError("Artefact store is unresolved")
        metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
        path = artefacts.publish(args.source, Path(config["artefact_root"]), args.stage,
                                 args.run_id, metadata)
        return {"published": str(path), "verified": True}
    if args.command == "smoke" and args.action == "fake":
        local_path(args.output)
        return smoke_a(FakeBackend(), args.output, {"synthetic_only": True}, "fake-local",
                       atol=1e-6, rtol=1e-6)
    if args.command == "features" and args.action == "fake-build":
        return feature_operations.fake_build(args)
    if args.command == "features" and args.action == "fake-build-families":
        return family_features.fake_build_families(args)
    if args.command == "features" and args.action == "check-families":
        return family_features.check_families_command(args)
    if args.command == "conformance" and args.action == "fake-released-test":
        local_path(args.archive)
        local_path(args.output)
        return evaluate_released_test(FakeBackend(), args.archive, args.output, {"synthetic_only": True},
                                      "fake-local", records=args.records)
    if args.command == "evaluation" and args.action == "bow-baseline":
        return bow_baseline_command(args)
    if args.command == "evaluation":
        local_path(args.artefact)
        local_path(args.output)
        experiment = load_config(args.experiment)
        result = leak_excluded_report(
            args.artefact, threshold=float(experiment.get("threshold", 0.5)),
            near_duplicate_threshold=float(experiment["near_duplicate_threshold"]))
        write_json(args.output, result)
        return result
    if args.command == "m0" and args.action == "fake-run":
        return phase4_operations.fake_run(args)
    try:
        profile, evidence = _gate(args)
    except PreflightError as error:
        if args.command == "environment":
            write_json(args.output, error.report)
        raise
    if args.command == "environment":
        write_json(args.output, evidence)
        return evidence
    if args.command == "features" and args.action == "build-families":
        return family_features.build_families(args, profile, evidence)
    if args.command == "features":
        return feature_operations.build(args, profile, evidence)
    if args.command == "m0":
        phase4_operations.prepare_environment()
    spec = load_config(args.release)
    if args.command == "upstream":
        if args.action == "fetch-cad":
            fetch_release(spec, args.source, allow_network=args.allow_network)
        result = validate_release(spec, args.source, load_model=True)
        result["preflight"] = evidence
        write_json(args.output, result)
        return result
    started = time.perf_counter()
    receipt = None
    if args.action == "run-b":
        receipt = artefacts.verify_restored(args.receipt, args.destination)
    source_manifest = validate_release(spec, args.source, load_model=True)
    validation_seconds = time.perf_counter() - started
    if not args.resources.exists():
        prepare_resources(profile, args.resources, allow_network=args.allow_network)
    smoke_operations.PROGRESS_PATH = local_path(args.workspace) / PROGRESS_RECORD
    smoke_operations.PROGRESS_PATH.unlink(missing_ok=True)
    backend = RealBackend(profile, args.source, spec, args.resources, evidence,
                          model_bundle=args.model_bundle, allow_network=args.allow_network)
    if args.command == "m0":
        result = phase4_operations.run(args, profile, evidence, backend, spec)
        result["source_manifest"] = source_manifest
        result["validation_seconds"] = validation_seconds
        write_json(args.output / "source_manifest.json", source_manifest)
        return result
    if args.command == "conformance":
        result = evaluate_released_test(backend, args.source / ARCHIVE, args.output, evidence,
                                        runtime_identity(), records=args.records,
                                        domains=tuple(args.domains))
        result["validation_seconds"] = validation_seconds
        write_json(args.output / "source_manifest.json", source_manifest)
        return result
    if args.action == "run-a":
        tolerance = profile.get("tolerance", {})
        if tolerance.get("atol") is None or tolerance.get("rtol") is None:
            raise ValueError("Determinism tolerances must be approved explicitly")
        return smoke_a(backend, args.output, evidence, runtime_identity(), **tolerance,
                       source_manifest=source_manifest, validation_seconds=validation_seconds)
    result = smoke_b(backend, args.destination, evidence, runtime_identity())
    result["source_manifest"] = source_manifest
    result["parent_artefact_manifest_sha256"] = receipt["source_manifest_sha256"]
    result["validation_seconds"] = validation_seconds
    write_json(args.output, result)
    write_json(args.output.parent / "source_manifest.json", source_manifest)
    return result


def record_failure(args, error: BaseException) -> None:
    """Write only fixed command labels and the exception class name, never its text."""
    workspace = getattr(args, "workspace", None)
    if workspace is None or not Path(workspace).is_dir():
        return
    try:
        record = Path(workspace) / FAILURE_RECORD
        record.unlink(missing_ok=True)
        write_json(record, {"command": args.command, "action": getattr(args, "action", None),
                            "exception_type": type(error).__name__})
    except (OSError, ValueError):
        return


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        result = execute(args)
        print(canonical_json(result))
        return 0
    except (ValueError, OSError, KeyError, TypeError, AssertionError, RuntimeError, subprocess.SubprocessError) as error:
        record_failure(args, error)
        print(f"Operation refused ({type(error).__name__}); verify inputs and approved stage prerequisites.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())