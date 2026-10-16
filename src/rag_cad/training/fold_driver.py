"""Fold-and-seed training driver of Phase 7 (D-20261017-55, D-20261013-28).

One artefact directory per cell under <output>/cells/:

    n0_released/                         the released checkpoint, scored, never trained
    m0_base/seed_<s>/                    D0 alone, once per seed
    m1_random|m2_keyword|m3_semantic/round_<k>/seed_<s>/
                                         D0 plus the round's training families of the condition

Every cell holds heldout_rows.jsonl and heldout_records.jsonl (all four record kinds of the
round's held-out families; every family for N0 and M0, which contain no family data, with the
fold recorded per row), released_test_rows.jsonl and released_test_metrics.json (the released CAD
test, scored in full and with the leaked records excluded as evaluation leak-excluded does), the
checkpoint of a trained cell, and manifest.json, written last: a cell is complete when its manifest
exists and every file hash in it verifies. A rerun skips complete cells, removes and redoes
incomplete ones, and refuses a cell whose manifest records another configuration.

Training reuses the existing trainers (TorchTrainer on CPU, or FakeTrainer for plumbing) and the
fixed recipe of configs/experiment.yaml; an epochs override is recorded in every manifest and in
the configuration fingerprint, so cells of different recipes never mix.
"""

import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from rag_cad.cad.feature_store import row_digest
from rag_cad.data.conditions import PRIMARY
from rag_cad.data.jsonl import read_jsonl, write_jsonl
from rag_cad.evaluation.offline import prediction_rows
from rag_cad.evaluation.posthoc import (
    ADAPTED_TEST,
    ADAPTED_TRAIN,
    exclusion_metrics,
    exclusion_sets,
    leaked_test_records,
)
from rag_cad.operations.paths import local_path
from rag_cad.operations.provenance import digest, sha256, write_json
from rag_cad.training.two_cache import RECORD_KINDS, TwoCache, held_out_set, training_set

STAGE = "phase7_fold_training"
SCHEMA = "rag_cad.fold_cell/1"
RUN_SCHEMA = "rag_cad.fold_run/1"
N0 = "n0_released"
M0 = "m0_base"
CONDITIONS = (N0, M0) + PRIMARY
CELL_MANIFEST = "manifest.json"
RUN_FILE = "run.json"
LEAKED_FILE = "leaked.json"
HELD_ROWS = "heldout_rows.jsonl"
HELD_RECORDS = "heldout_records.jsonl"
TEST_ROWS = "released_test_rows.jsonl"
TEST_METRICS = "released_test_metrics.json"
BREAKDOWN_FIELDS = ("semantic_role", "attack_category", "cue_position")


def cell_list(conditions, seeds, rounds) -> list[dict]:
    """N0 once; M0 once per seed; M1 to M3 once per round and per seed."""
    unknown = set(conditions) - set(CONDITIONS)
    if unknown:
        raise ValueError(f"Unknown conditions: {sorted(unknown)}")
    cells = []
    for condition in CONDITIONS:
        if condition not in conditions:
            continue
        if condition == N0:
            cells.append({"condition": N0, "round": None, "seed": None})
        elif condition == M0:
            cells.extend({"condition": M0, "round": None, "seed": seed} for seed in seeds)
        else:
            cells.extend({"condition": condition, "round": round_number, "seed": seed}
                         for round_number in rounds for seed in seeds)
    return cells


def cell_name(cell: dict) -> str:
    parts = [cell["condition"]]
    if cell["round"] is not None:
        parts.append(f"round_{cell['round']}")
    if cell["seed"] is not None:
        parts.append(f"seed_{cell['seed']}")
    return "/".join(parts)


def cell_complete(directory: Path, fingerprint: str) -> dict | None:
    """The manifest of a complete cell of this configuration, None when absent or incomplete;
    refuses a complete cell of another configuration."""
    import json

    manifest_path = directory / CELL_MANIFEST
    if not manifest_path.is_file():
        return None
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("config_fingerprint") != fingerprint:
        raise ValueError(f"Cell {directory.name} was written under another configuration")
    for name, expected in manifest["files"].items():
        if not (directory / name).is_file() or sha256(directory / name) != expected:
            return None
    return manifest


def leaked_records(phase4_root: Path, near_duplicate_threshold: float) -> dict:
    root = local_path(phase4_root)
    if not (root / ADAPTED_TRAIN).is_file() or not (root / ADAPTED_TEST).is_file():
        raise ValueError("The Phase 4 root must hold its adapted D0 train and test records")
    return leaked_test_records(read_jsonl(root / ADAPTED_TRAIN), read_jsonl(root / ADAPTED_TEST),
                               near_duplicate_threshold=near_duplicate_threshold)


def _check(probabilities: np.ndarray, rows: int) -> np.ndarray:
    probabilities = np.asarray(probabilities, dtype=np.float32)
    if probabilities.shape != (rows, 2) or not np.isfinite(probabilities).all():
        raise ValueError("Head produced misaligned or non-finite probabilities")
    if rows > 1 and np.ptp(probabilities[:, 1]) == 0:
        raise ValueError("Head produced constant probabilities")
    return probabilities


def held_out_rows(cache: TwoCache, rows: list[dict], scores: np.ndarray, threshold: float) -> list[dict]:
    result = []
    for row, score in zip(rows, scores):
        fold = cache.folds[row["group_id"]]
        result.append({"record_id": row["record_id"], "sentence_id": row["sentence_id"],
                       "group_id": row["group_id"], "family_id": fold["family_id"], "fold": fold["fold"],
                       "record_kind": RECORD_KINDS[row["condition_source"]],
                       "condition_source": row["condition_source"], "label": int(row["label"]),
                       "is_target": bool(row["is_target"]), "probability": float(score),
                       "decision": bool(score > threshold)})
    return result


def held_out_records(cache: TwoCache, rows: list[dict], threshold: float) -> list[dict]:
    """Per record: the maximum sentence probability (the passage filter's view: the record is
    flagged when any sentence is removed) and, where the record has one, its target sentence's."""
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row["record_id"], []).append(row)
    records = []
    for record_id in sorted(grouped):
        members = grouped[record_id]
        first = members[0]
        targets = [row["probability"] for row in members if row["is_target"]]
        if len(targets) > 1:
            raise ValueError(f"Record {record_id} has more than one target sentence")
        target = targets[0] if targets else None
        highest = max(row["probability"] for row in members)
        fold = cache.folds[first["group_id"]]
        records.append({"record_id": record_id, "group_id": first["group_id"], "family_id": fold["family_id"],
                        "fold": fold["fold"], "record_kind": first["record_kind"],
                        **{name: fold[name] for name in BREAKDOWN_FIELDS},
                        "label": int(any(row["label"] for row in members)), "sentences": len(members),
                        "max_probability": highest, "flagged": bool(highest > threshold),
                        "flagged_rows": sum(row["decision"] for row in members),
                        "target_probability": target,
                        "target_flagged": None if target is None else bool(target > threshold)})
    return records


class ReleasedScorer:
    """N0: the released checkpoint verified by hash and scored as it is (torch), or the fake
    backend's deterministic scorer for plumbing runs."""

    def __init__(self, kind: str, checkpoint: Path | None = None, expected_sha256: str | None = None):
        self.kind = kind
        if kind == "torch":
            from rag_cad.cad.upstream_adapter import load_checkpoint

            if checkpoint is None or not expected_sha256:
                raise ValueError("N0 needs the released checkpoint and its pinned hash")
            self.model = load_checkpoint(checkpoint, expected_sha256)
            self.sha256 = expected_sha256
        elif kind == "fake":
            from rag_cad.operations.smoke import FakeBackend

            self.model = FakeBackend()
            self.sha256 = "fake-local"
        else:
            raise ValueError("Unknown released scorer")

    def __call__(self, features: np.ndarray) -> np.ndarray:
        if self.kind == "fake":
            return self.model.reference_score(features)
        import torch

        with torch.no_grad():
            chunks = [torch.softmax(self.model(torch.from_numpy(np.ascontiguousarray(
                features[start:start + 4096], dtype=np.float32))), dim=-1).numpy()
                for start in range(0, len(features), 4096)]
        return np.concatenate(chunks)


def run_cell(cache: TwoCache, cell: dict, directory: Path, *, trainer, released, recipe: dict, config: dict,
             fingerprint: str, exclusions: dict, provenance: dict) -> dict:
    started = time.perf_counter()
    threshold = recipe["threshold"]
    condition, round_number, seed = cell["condition"], cell["round"], cell["seed"]
    directory.mkdir(parents=True, exist_ok=False)
    held = held_out_set(cache, round_number if condition in PRIMARY else None)
    training, train_seconds, checkpoint, history, counts = None, 0.0, None, None, None
    if condition == N0:
        score = released
        counts = {"d0_rows": 0, "family_rows": 0, "training_families": 0}
    else:
        training, counts = training_set(cache, condition, round_number if condition in PRIMARY else None)
        fit_started = time.perf_counter()
        trained = trainer.fit(training.features, training.labels, seed=seed)
        train_seconds = time.perf_counter() - fit_started
        history = trained["history"]
        metadata = {"hidden": list(recipe["architecture"]["hidden"]), "threshold": threshold,
                    "condition": condition, "round": round_number, "seed": seed, "trainer": trainer.kind,
                    **{name: cache.summary["identities"]["phase4"][name]
                       for name in ("representation_id", "encoder_revision", "encoder_code_revision", "segmenter")},
                    "mode": cache.mode, "config_fingerprint": fingerprint, "git_commit": provenance["commit"],
                    "train_row_digest": row_digest(training.rows),
                    "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        path = directory / trainer.checkpoint_file
        checkpoint = {"file": trainer.checkpoint_file, "sha256": trainer.save(trained, path, metadata)}

        def score(features):
            return trainer.predict(trained, features)

        reloaded = trainer.reload_predict(path, checkpoint["sha256"], held.features)
        if not np.allclose(reloaded, score(held.features), atol=1e-5, rtol=1e-4):
            raise ValueError("Reloaded checkpoint does not reproduce its predictions")
    predict_started = time.perf_counter()
    held_probabilities = _check(score(held.features), len(held.rows))
    test = cache.released_test
    test_probabilities = _check(score(test.features), len(test.rows))
    predict_seconds = time.perf_counter() - predict_started
    rows = held_out_rows(cache, held.rows, held_probabilities[:, 1], threshold)
    records = held_out_records(cache, rows, threshold)
    write_jsonl(directory / HELD_ROWS, rows)
    write_jsonl(directory / HELD_RECORDS, records)
    test_rows = prediction_rows(test.rows, test.labels, test_probabilities, threshold=threshold)
    write_jsonl(directory / TEST_ROWS, test_rows)
    metrics = exclusion_metrics(test.labels, test_probabilities[:, 1], [row["upstream_mask"] for row in test_rows],
                                [row["record_id"] for row in test.rows], exclusions, threshold=threshold)
    write_json(directory / TEST_METRICS, metrics)
    kinds: dict[str, int] = {}
    for record in records:
        kinds[record["record_kind"]] = kinds.get(record["record_kind"], 0) + 1
    files = [HELD_ROWS, HELD_RECORDS, TEST_ROWS, TEST_METRICS] + ([checkpoint["file"]] if checkpoint else [])
    manifest = {"schema": SCHEMA, "stage": STAGE, "cell": cell_name(cell), "condition": condition,
                "round": round_number, "seed": seed, "mode": cache.mode, "config_fingerprint": fingerprint,
                "config": config, "identity": cache.identity_check, "provenance": provenance,
                "trainer": None if condition == N0 else trainer.kind,
                "checkpoint": checkpoint or {"released_sha256": released.sha256},
                "training_rows": counts if training is None else {**counts, "rows": len(training.rows),
                                                                  "malicious_rows": int(training.labels.sum())},
                "held_out": {"rows": len(rows), "records": len(records), "records_by_kind": kinds,
                             "families": len({record["group_id"] for record in records}),
                             "folds": sorted({record["fold"] for record in records})},
                "released_test_rows": len(test_rows),
                "history": None if history is None else {
                    "epochs": len(history["epoch_mean_loss"]), "final_epoch_loss": history["epoch_mean_loss"][-1],
                    "first_epoch_loss": history["epoch_mean_loss"][0], "device": history.get("device")},
                "timings_seconds": {"train": train_seconds, "predict": predict_seconds,
                                    "total": time.perf_counter() - started},
                "files": {name: sha256(directory / name) for name in files},
                "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    write_json(directory / CELL_MANIFEST, manifest)
    return manifest


def run_folds(cache: TwoCache, output: Path, *, trainer, released, recipe: dict, cells: list[dict], leaked: dict,
              config: dict, provenance: dict, log=lambda message: None) -> dict:
    """Run every cell not yet complete; returns the per-cell status and timings."""
    import json

    output = local_path(output)
    fingerprint = digest(config)
    run_path = output / RUN_FILE
    if run_path.is_file():
        existing = json.loads(run_path.read_text(encoding="utf-8"))
        if existing.get("config_fingerprint") != fingerprint:
            raise ValueError("Output holds a run of another configuration; use a new output directory")
    else:
        output.mkdir(parents=True, exist_ok=True)
        write_json(output / LEAKED_FILE, leaked)
        write_json(run_path, {"schema": RUN_SCHEMA, "stage": STAGE, "config_fingerprint": fingerprint,
                              "config": config, "identity_check": cache.identity_check, "cache": cache.summary,
                              "provenance": provenance, "leaked_sha256": sha256(output / LEAKED_FILE)})
    exclusions = exclusion_sets(leaked)
    statuses = []
    started = time.perf_counter()
    for cell in cells:
        directory = output / "cells" / cell_name(cell)
        manifest = cell_complete(directory, fingerprint)
        if manifest is not None:
            statuses.append({"cell": cell_name(cell), "status": "skipped_complete",
                             "seconds": manifest["timings_seconds"]["total"]})
            log(f"{cell_name(cell)}: complete, skipped")
            continue
        if directory.exists():
            shutil.rmtree(directory)
        manifest = run_cell(cache, cell, directory, trainer=trainer, released=released, recipe=recipe,
                            config=config, fingerprint=fingerprint, exclusions=exclusions, provenance=provenance)
        statuses.append({"cell": cell_name(cell), "status": "ran", **manifest["timings_seconds"]})
        log(f"{cell_name(cell)}: ran in {manifest['timings_seconds']['total']:.1f} s")
    ran = [status for status in statuses if status["status"] == "ran"]
    report = {"schema": RUN_SCHEMA, "stage": STAGE, "output": str(output), "config_fingerprint": fingerprint,
              "cells": statuses, "ran": len(ran), "skipped": len(statuses) - len(ran),
              "seconds": time.perf_counter() - started,
              "mean_cell_seconds": (sum(status["total"] for status in ran) / len(ran)) if ran else None,
              "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    write_json(output / "reports" / f"run_{stamp}.json", report)
    return report


def run_folds_command(args) -> dict:
    """CLI body of training run-folds."""
    import sys

    from rag_cad.config import load_config
    from rag_cad.data.schema import ContractError
    from rag_cad.operations.provenance import git_output
    from rag_cad.training.recipe import training_recipe
    from rag_cad.training.two_cache import load_two_caches

    output = local_path(args.output)
    repo = Path(args.repo).resolve()
    for source in (args.phase4_root, args.families, repo):
        source = local_path(source)
        if output.is_relative_to(source) or source.is_relative_to(output):
            raise ValueError("Output must lie outside the repository and both feature caches")
    experiment = load_config(args.experiment)
    recipe = training_recipe(experiment)
    if args.epochs is not None:
        if isinstance(args.epochs, bool) or args.epochs < 1:
            raise ValueError("Epochs must be a positive integer")
        recipe = {**recipe, "epochs": args.epochs, "primary_checkpoint_epoch": args.epochs}
    mode = args.mode or experiment.get("representation")
    seeds = list(recipe["seeds"]) if args.seeds is None else list(args.seeds)
    if not seeds or len(set(seeds)) != len(seeds) or any(seed not in recipe["seeds"] for seed in seeds):
        raise ValueError("Seeds must be a non-empty subset of the experiment seeds")
    fold_rows = read_jsonl(local_path(args.folds))
    try:
        cache = load_two_caches(args.phase4_root, args.families, mode, fold_rows)
    except ContractError as error:
        output.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        write_json(output / f"identity_refused_{stamp}.json", error.report)
        raise
    rounds = cache.rounds if args.rounds is None else sorted(set(args.rounds))
    if set(rounds) - set(cache.rounds):
        raise ValueError("Rounds must name folds of the table")
    cells = cell_list(args.conditions, seeds, rounds)
    if args.trainer == "torch":
        import torch

        from rag_cad.training.torch_trainer import TorchTrainer

        if args.threads:
            torch.set_num_threads(args.threads)
        trainer = TorchTrainer(recipe, device="cpu")
        spec = load_config(args.release)
        released = ReleasedScorer("torch", local_path(args.released_checkpoint),
                                  spec["files"]["classifier_fullcad.pt"]["sha256"]) if N0 in args.conditions else None
        runtime = {"torch": torch.__version__, "threads": torch.get_num_threads(), "device": "cpu"}
    else:
        from rag_cad.training.fake_trainer import FakeTrainer

        trainer = FakeTrainer(recipe)
        released = ReleasedScorer("fake")
        runtime = {"torch": None, "threads": None, "device": "fake"}
    try:
        commit = git_output(repo, "rev-parse", "HEAD")
    except (ValueError, OSError):
        commit = "unknown"
    near = float(experiment["near_duplicate_threshold"])
    config = {"mode": mode, "trainer": trainer.kind, "device": "cpu" if trainer.kind == "torch" else "fake",
              "recipe": {key: value for key, value in recipe.items() if key != "seeds"},
              "epochs_override": args.epochs, "threshold": recipe["threshold"],
              "near_duplicate_threshold": near, "folds_sha256": sha256(local_path(args.folds)),
              "released_checkpoint_sha256": None if released is None else released.sha256,
              "cache": {key: cache.summary[key] for key in ("d0_row_digest", "released_test_row_digest",
                                                            "assembled_row_digests", "family_rows")},
              "identity": {name: cache.summary["identities"]["phase4"][name]
                           for name in ("representation_id", "encoder_revision", "encoder_code_revision",
                                        "segmenter", "dtype")}}
    provenance = {"commit": commit, "runtime": runtime, "phase4_root": str(local_path(args.phase4_root)),
                  "family_root": str(local_path(args.families))}
    report = run_folds(cache, output, trainer=trainer, released=released, recipe=recipe, cells=cells,
                       leaked=leaked_records(args.phase4_root, near), config=config, provenance=provenance,
                       log=lambda message: print(message, file=sys.stderr, flush=True))
    return {**report, "planned_cells": len(cells), "mode": mode, "epochs": recipe["epochs"],
            "identity_matches": cache.identity_check["matches"], "cache": {
                key: cache.summary[key] for key in ("d0_rows", "released_test_rows", "family_rows", "groups")}}
