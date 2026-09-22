"""Feature-build commands: fake CPU plumbing and the gated real build."""

import json
from pathlib import Path

from rag_cad.cad.feature_builder import FeatureBuilder, build_condition
from rag_cad.config import load_config
from rag_cad.data.jsonl import load_records
from rag_cad.operations.paths import local_path
from rag_cad.operations.provenance import digest


def _inputs(args):
    local_path(args.output)
    experiment = load_config(args.experiment)
    records, inventory = load_records(args.input)
    manifest = json.loads(local_path(args.manifest).read_text(encoding="utf-8"))
    return experiment, records, inventory, manifest


def _result(kind: str, args, inventory: dict, assembled: dict) -> dict:
    return {"execution_kind": kind, "condition": args.condition, "split": args.split,
            "input": inventory, "assembled": {"name": assembled["name"], "counts": assembled["counts"],
                                              "identity": assembled["identity"],
                                              "parents": assembled["parents"],
                                              "row_digest": assembled["row_digest"]},
            "output": str(Path(args.output).resolve())}


def fake_build(args) -> dict:
    """CPU plumbing only: synthetic identity, deterministic fake encoder, no scientific meaning."""
    from rag_cad.cad.fake_encoder import FAKE_REPRESENTATION, FakeEncoder

    experiment, records, inventory, manifest = _inputs(args)
    builder = FeatureBuilder(FAKE_REPRESENTATION, FakeEncoder(), feature_environment_id="fake-local",
                             commit="fake-local", config_sha256=digest(experiment))
    assembled = build_condition(builder, records, manifest, args.condition, args.split, args.output,
                                shard_records=args.shard_records, resume=args.resume)
    return _result("fake", args, inventory, assembled)


def build(args, profile: dict, evidence: dict) -> dict:
    """Real build behind the final-stage gate: tested profile, approved budget, resolved representation."""
    from rag_cad.cad.representation import JinaEncoder, RepresentationConfig
    from rag_cad.operations.upstream import validate_resources

    experiment, records, inventory, manifest = _inputs(args)
    mode = experiment.get("representation")
    if mode is None:
        raise ValueError("Primary representation is unresolved (D-20260921-05)")
    if mode != profile["expected"]["representation"]:
        raise ValueError("Experiment representation differs from the tested profile; rerun the gate in that mode")
    representation = RepresentationConfig.from_profile(profile, mode=mode)
    for path in (args.resources, args.model_bundle):
        local_path(path, args.workspace)
    import nltk

    validate_resources(profile, args.resources)
    nltk.data.path[:] = [str(args.resources)]
    encoder = JinaEncoder(representation.encoder_revision, representation.encoder_code_revision,
                          args.model_bundle, allow_network=args.allow_network, allow_remote_code=True)
    builder = FeatureBuilder(representation, encoder, feature_environment_id=evidence["environment_id"],
                             commit=args.commit, config_sha256=digest(experiment))
    assembled = build_condition(builder, records, manifest, args.condition, args.split, args.output,
                                shard_records=args.shard_records, resume=args.resume)
    return _result("real", args, inventory, assembled) | {"maximum_token_length": encoder.max_token_length}
