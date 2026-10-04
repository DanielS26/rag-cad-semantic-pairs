"""Phase 4 baseline stage: adapt the official D0, split it, build the M0 features, train M0 for
every declared seed and evaluate each seed and the released checkpoint on the released test
set, in one bounded run that publishes as a single artefact.

The fake twin runs the identical plumbing on CPU with the fake encoder and the fake trainer.
"""

import os
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import yaml

from rag_cad.cad.feature_builder import FeatureBuilder, build_condition
from rag_cad.cad.feature_store import read_feature_set
from rag_cad.config import load_config
from rag_cad.data.cad_release_adapter import OUTPUT_FILES, adapt_release
from rag_cad.data.commands import experiment_value
from rag_cad.data.jsonl import load_records, write_jsonl
from rag_cad.data.schema import ContractError
from rag_cad.data.split import assign_splits, check_leakage
from rag_cad.evaluation.offline import aggregate, evaluate_rows, prediction_rows
from rag_cad.operations.paths import local_path
from rag_cad.operations.provenance import digest, sha256, write_json
from rag_cad.operations.smoke import mark, resource_snapshot
from rag_cad.training.recipe import training_recipe

CONDITION = "m0_base"
REPORT = "phase4_report.json"
SPLIT_MANIFEST = "split_manifest.json"
RECIPE_KEYS = ("epochs", "batch_size", "optimizer", "learning_rate", "weight_decay", "schedule", "loss",
               "primary_checkpoint_epoch")


def prepare_environment() -> None:
    """Deterministic cuBLAS workspaces; must be set before the first CUDA matmul of the process."""
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")


def _records(adapted: Path) -> tuple[list[dict], dict]:
    records, inventory = [], {"files": {}, "records": 0}
    for kind in ("original_train", "original_test"):
        loaded, part = load_records(adapted / OUTPUT_FILES[kind])
        records.extend(loaded)
        inventory["files"].update(part["files"])
        inventory["records"] += part["records"]
    return records, inventory


def run_m0(trainer, builder: FeatureBuilder, spec: dict, source: Path, output: Path, experiment: dict, *,
           metadata: dict, identity: str, provenance: dict, reference_score=None, seeds=None,
           token_source=None) -> dict:
    """provenance holds the commit, lock hash and training environment id written into every checkpoint;
    token_source is the encoder or backend whose max_token_length is read once encoding has run."""
    recipe = training_recipe(experiment)
    seeds = list(recipe["seeds"]) if seeds is None else list(seeds)
    if not seeds or len(set(seeds)) != len(seeds) or any(seed not in recipe["seeds"] for seed in seeds):
        raise ValueError("Seeds must be a non-empty subset of the experiment seeds")
    local_path(output)
    output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    before = resource_snapshot(output)
    adaptation = adapt_release(spec, source, output / "adapted", include_paraphrased=False)
    mark("d0_adapted")
    records, inventory = _records(output / "adapted")
    manifest = assign_splits(records, experiment_value(experiment, "split_ratios"),
                             experiment_value(experiment, "split_seed"),
                             d0_holdout_policy=experiment_value(experiment, "d0_holdout_policy"))
    write_json(output / SPLIT_MANIFEST, manifest)
    split_hash = sha256(output / SPLIT_MANIFEST)
    mark("d0_split_assigned")
    try:
        leakage = {"refused": False, **check_leakage(
            records, manifest, near_duplicate_threshold=experiment_value(experiment, "near_duplicate_threshold"))}
    except ContractError as error:
        leakage = {"refused": True, "note": "The released train/test split is kept as published; its "
                                            "leakage report is recorded here, not enforced.", **error.report}
    features_root = output / "features"
    build_condition(builder, records, manifest, CONDITION, "train", features_root)
    mark("m0_train_features_built")
    build_condition(builder, records, manifest, "common", "test", features_root, resume=True)
    mark("m0_test_features_built")
    train_features, train_labels, _, train_manifest = read_feature_set(
        features_root / "assembled" / CONDITION / "train")
    test_features, test_labels, test_rows, test_manifest = read_feature_set(
        features_root / "assembled" / "common" / "test")
    threshold = recipe["threshold"]
    models = {}
    for seed in seeds:
        fit_started = time.perf_counter()
        trained = trainer.fit(train_features, train_labels, seed=seed)
        fit_seconds = time.perf_counter() - fit_started
        directory = output / "models" / CONDITION / f"seed_{seed}"
        directory.mkdir(parents=True, exist_ok=False)
        probabilities = trainer.predict(trained, test_features)
        if not np.isfinite(probabilities).all() or np.ptp(probabilities[:, 1]) == 0:
            raise ValueError("Trained head produced non-finite or constant probabilities")
        checkpoint_metadata = {
            "hidden": list(recipe["architecture"]["hidden"]), "threshold": threshold,
            "condition": CONDITION, "seed": seed, "trainer": trainer.kind,
            "representation_id": builder.identity["representation_id"],
            "encoder_revision": builder.identity["encoder_revision"],
            "encoder_code_revision": builder.identity["encoder_code_revision"],
            "segmenter": builder.identity["segmenter"],
            "dataset_manifest_sha256": split_hash, "git_commit": provenance["commit"],
            "lock_sha256": provenance["lock_sha256"],
            "feature_environment_id": builder.identity["feature_environment_id"],
            "training_environment_id": provenance["training_environment_id"],
            "config_sha256": builder.identity["config_sha256"],
            "train_feature_row_digest": train_manifest["row_digest"],
            "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        checkpoint_hash = trainer.save(trained, directory / trainer.checkpoint_file, checkpoint_metadata)
        reloaded = trainer.reload_predict(directory / trainer.checkpoint_file, checkpoint_hash, test_features)
        if reloaded.shape != probabilities.shape or not np.allclose(reloaded, probabilities, atol=1e-5, rtol=1e-4):
            raise ValueError("Reloaded checkpoint does not reproduce its predictions")
        evaluation = evaluate_rows(test_labels, probabilities, test_rows, threshold=threshold)
        write_jsonl(directory / "test_predictions.jsonl",
                    prediction_rows(test_rows, test_labels, probabilities, threshold=threshold))
        write_json(directory / "train_manifest.json",
                   {"split_manifest_sha256": split_hash, "train_feature_set": train_manifest,
                    "test_feature_set": test_manifest})
        resolved = {"condition": CONDITION, "seed": seed, "representation": experiment.get("representation"),
                    "architecture": recipe["architecture"], "threshold": threshold,
                    "training": {key: recipe[key] for key in RECIPE_KEYS}}
        (directory / "config.resolved.yaml").write_text(yaml.safe_dump(resolved, sort_keys=True), encoding="utf-8")
        write_json(directory / "run_metadata.json",
                   {**checkpoint_metadata, "checkpoint_sha256": checkpoint_hash, "history": trained["history"],
                    "fit_seconds": fit_seconds, "evaluation": evaluation})
        models[str(seed)] = {"checkpoint_sha256": checkpoint_hash, "fit_seconds": fit_seconds,
                             "final_epoch_loss": trained["history"]["epoch_mean_loss"][-1],
                             "evaluation": evaluation}
    mark("m0_trained")
    reference = None
    if reference_score is not None:
        reference_probabilities = np.asarray(reference_score(test_features), dtype=np.float32)
        reference = evaluate_rows(test_labels, reference_probabilities, test_rows, threshold=threshold)
        write_jsonl(output / "reference_checkpoint_test_predictions.jsonl",
                    prediction_rows(test_rows, test_labels, reference_probabilities, threshold=threshold))
    mark("m0_evaluated")
    summary_keys = ("name", "counts", "row_digest", "parents")
    report = {"execution_kind": trainer.kind, "stage": "phase4_m0", "runtime_identity": identity,
              "metadata": metadata,
              "adaptation": {name: {key: entry[key] for key in ("kind", "sha256", "counts", "dataset_digest",
                                                                 "records_sha256", "groups", "suites")}
                             for name, entry in adaptation["files"].items()},
              "input": inventory,
              "split": {"manifest_sha256": split_hash, "seed": manifest["seed"], "ratios": manifest["ratios"],
                        "d0_holdout_policy": manifest["d0_holdout_policy"], "counts": manifest["counts"],
                        "pinned_groups": len(manifest["pinned_groups"])},
              "upstream_split_leakage": leakage,
              "features": {"identity": builder.identity,
                           "train": {key: train_manifest[key] for key in summary_keys},
                           "test": {key: test_manifest[key] for key in summary_keys}},
              "recipe": recipe, "seeds": seeds, "models": models,
              "aggregate": aggregate({seed: entry["evaluation"] for seed, entry in models.items()}),
              "reference_checkpoint": reference,
              "maximum_token_length": getattr(token_source, "max_token_length", None),
              "timings_seconds": {"total": time.perf_counter() - started,
                                  "fit": {seed: entry["fit_seconds"] for seed, entry in models.items()}},
              "resources_before": before, "resources_after": resource_snapshot(output)}
    if trainer.kind == "torch" and trainer.device.startswith("cuda"):
        report["peak_gpu_memory_bytes"] = trainer.torch.cuda.max_memory_allocated()
    write_json(output / REPORT, report)
    mark("phase4_report_written")
    return report


def fake_run(args) -> dict:
    """CPU plumbing only: fake encoder, fake trainer, synthetic identity, no scientific meaning."""
    from rag_cad.cad.fake_encoder import FAKE_REPRESENTATION, FakeEncoder
    from rag_cad.operations.smoke import FakeBackend
    from rag_cad.operations.upstream import validate_release_spec
    from rag_cad.training.fake_trainer import FakeTrainer

    local_path(args.source)
    local_path(args.output)
    experiment = load_config(args.experiment)
    spec = load_config(args.release)
    validate_release_spec(spec)
    encoder = FakeEncoder()
    builder = FeatureBuilder(FAKE_REPRESENTATION, encoder, feature_environment_id="fake-local",
                             commit="fake-local", config_sha256=digest(experiment))
    return run_m0(FakeTrainer(training_recipe(experiment)), builder, spec, args.source, args.output, experiment,
                  metadata={"synthetic_only": True}, identity="fake-local",
                  provenance={"commit": "fake-local", "lock_sha256": "fake-local",
                              "training_environment_id": "fake-local"},
                  reference_score=FakeBackend().reference_score, seeds=args.seeds or None,
                  token_source=encoder)


def run(args, profile: dict, evidence: dict, backend, spec: dict) -> dict:
    """The real stage behind the final-stage gate: tested profile, approved budget, GPU runtime."""
    from rag_cad.cad.representation import RepresentationConfig
    from rag_cad.operations.smoke import runtime_identity
    from rag_cad.training.torch_trainer import TorchTrainer

    experiment = load_config(args.experiment)
    mode = experiment.get("representation")
    if mode is None:
        raise ValueError("Primary representation is unresolved (D-20260921-05)")
    if mode != profile["expected"]["representation"]:
        raise ValueError("Experiment representation differs from the tested profile; rerun the gate in that mode")
    representation = RepresentationConfig.from_profile(profile, mode=mode)
    builder = FeatureBuilder(representation, backend.encoder, feature_environment_id=evidence["environment_id"],
                             commit=args.commit, config_sha256=digest(experiment))
    trainer = TorchTrainer(training_recipe(experiment))
    if not trainer.device.startswith("cuda"):
        raise ValueError("Phase 4 training requires the approved GPU runtime")
    return run_m0(trainer, builder, spec, args.source, args.output, experiment, metadata=evidence,
                  identity=runtime_identity(),
                  provenance={"commit": args.commit, "lock_sha256": profile["expected"]["lock_sha256"],
                              "training_environment_id": evidence["environment_id"]},
                  reference_score=backend.reference_score, token_source=backend)
