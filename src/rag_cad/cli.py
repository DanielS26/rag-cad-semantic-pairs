"""Phase 1A command surface; real execution requires explicit reviewed inputs."""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from rag_cad.config import load_config
from rag_cad.operations import artefacts
from rag_cad.operations.paths import execution_paths, local_path
from rag_cad.operations.preflight import PreflightError, preflight
from rag_cad.operations.provenance import canonical_json, sha256, verify_upstream, write_json
from rag_cad.operations.smoke import FakeBackend, RealBackend, runtime_identity, smoke_a, smoke_b
from rag_cad.operations.upstream import fetch_release, prepare_resources, validate_release


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
    if args.command == "smoke":
        if profile.get("remote_code_approved") is not True:
            raise ValueError("Remote-code execution requires explicit profile approval")
        tolerance = profile.get("tolerance", {})
        if any(type(tolerance.get(key)) not in (float, int) or not 0 <= tolerance[key] <= 0.001
               for key in ("atol", "rtol")):
            raise ValueError("Explicit bounded smoke tolerances are required")
    stage = args.stage if args.command == "environment" else "smoke"
    evidence = preflight(args.repo, args.commit, profile, stage, args.lock, args.workspace)
    return profile, evidence


def execute(args) -> dict:
    if args.command == "audit":
        return verify_upstream(args.repo)
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
    try:
        profile, evidence = _gate(args)
    except PreflightError as error:
        if args.command == "environment":
            write_json(args.output, error.report)
        raise
    if args.command == "environment":
        write_json(args.output, evidence)
        return evidence
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
    backend = RealBackend(profile, args.source, spec, args.resources, evidence,
                          model_bundle=args.model_bundle, allow_network=args.allow_network)
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


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        result = execute(args)
        print(canonical_json(result))
        return 0
    except (ValueError, OSError, KeyError, TypeError, AssertionError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"Operation refused ({type(error).__name__}); verify inputs and approved stage prerequisites.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())