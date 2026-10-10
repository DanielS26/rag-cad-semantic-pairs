"""CPU data commands: validate, split, check-leakage and compare-budgets."""

import json
from pathlib import Path

from rag_cad.config import load_config
from rag_cad.data.conditions import compare_budgets
from rag_cad.data.families import prescreen
from rag_cad.data.jsonl import load_records, read_jsonl
from rag_cad.data.schema import ContractError
from rag_cad.data.split import apply_manifest, assign_splits, check_leakage
from rag_cad.data.validate import validate_dataset
from rag_cad.operations.paths import local_path
from rag_cad.operations.provenance import write_json


def experiment_value(config: dict, key: str):
    """Experiment values are decisions; a null value is unresolved and refuses execution."""
    value = config.get(key)
    if value is None:
        raise ValueError(f"Unresolved experiment value: {key}")
    return value


def frozen_tokenizer(profile_path: Path | None, resources: Path | None):
    """The round trip must use the pinned, hash-verified segmenter resource, never a default."""
    if profile_path is None or resources is None:
        raise ValueError("Round trip requires the approved profile and verified segmenter resources")
    from rag_cad.operations.upstream import validate_resources

    profile = load_config(profile_path)
    resources = local_path(resources)
    validate_resources(profile, resources)
    import nltk
    from nltk.tokenize import sent_tokenize

    nltk.data.path[:] = [str(resources)]
    return sent_tokenize


def adapt(args) -> dict:
    """Adapt the pinned CAD release archives into scorer records; CPU only, no profile needed."""
    from rag_cad.data.cad_release_adapter import adapt_release
    from rag_cad.operations.upstream import validate_release_spec

    spec = load_config(args.release)
    validate_release_spec(spec)
    return adapt_release(spec, local_path(args.source), local_path(args.output),
                         include_paraphrased=not args.skip_paraphrased)


def selfcheck(args) -> dict:
    """Run tools/selfcheck.py (DRAFTING_PROMPT v2 checker M0-M16 and S1-S12) with the same arguments.

    The tool writes its own report; a non-zero exit is raised as a ContractError carrying that
    report so the CLI exits 2. CPU only; the tool binds to this package's tokenisation.
    """
    import importlib.util

    script = local_path(Path(args.repo) / "tools" / "selfcheck.py")
    spec = importlib.util.spec_from_file_location("rag_cad_selfcheck", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    argv = ["--batch", str(local_path(args.batch)), "--manifest", str(local_path(args.manifest)),
            "--report", str(local_path(args.report)), "--stage", args.stage]
    for previous in args.previous:
        argv += ["--previous", str(local_path(previous))]
    if args.prompt is not None:
        argv += ["--prompt", str(local_path(args.prompt))]
    if args.semantic is not None:
        argv += ["--semantic", str(local_path(args.semantic))]
    if args.strict:
        argv.append("--strict")
    code = module.main(argv)
    report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    if code != 0:
        raise ContractError("Self-check failed; see the report", report)
    return report


def run(args) -> dict:
    if args.action == "adapt-cad":
        return adapt(args)
    if args.action == "selfcheck":
        return selfcheck(args)
    local_path(args.input)
    local_path(args.output)
    config = load_config(args.experiment)
    records, inventory = load_records(args.input)
    if args.action == "prescreen":
        entries = read_jsonl(local_path(args.families))
        tolerance = experiment_value(config, "benign_length_tolerance")
        try:
            result = prescreen(records, entries, length_tolerance=tolerance,
                               minimum_per_role=args.minimum_per_role)
        except ContractError as error:
            write_json(args.output, {"input": inventory, **error.report})
            raise
    elif args.action == "validate":
        tokenize = frozen_tokenizer(args.profile, args.resources) if args.roundtrip else None
        result = validate_dataset(records, tokenize=tokenize,
                                  near_duplicate_threshold=config.get("near_duplicate_threshold"))
    elif args.action == "split":
        result = assign_splits(records, experiment_value(config, "split_ratios"),
                               experiment_value(config, "split_seed"),
                               d0_holdout_policy=experiment_value(config, "d0_holdout_policy"))
    else:
        manifest = json.loads(local_path(args.manifest).read_text(encoding="utf-8"))
        try:
            if args.action == "check-leakage":
                result = check_leakage(records, manifest, near_duplicate_threshold=experiment_value(
                    config, "near_duplicate_threshold"))
            else:
                result = compare_budgets(apply_manifest(records, manifest), tuple(args.conditions),
                                         length_tolerance=experiment_value(config, "benign_length_tolerance"))
        except ContractError as error:
            write_json(args.output, {"input": inventory, **error.report})
            raise
    result = {"input": inventory, **result}
    write_json(args.output, result)
    return result
