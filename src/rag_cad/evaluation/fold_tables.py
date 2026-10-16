"""Result tables of the fold experiments (D-20261017-55 (c), D-20261016-49 (d)).

Reads a training run-folds output, verifies every cell, pools the held-out predictions over the
rounds per condition and seed, and reports per condition:

- twin false-alarm rate: share of semantic twins flagged;
- random and keyword control false-alarm rates: share of each control record flagged;
- malicious detection rate: share of malicious records flagged;
- within-family paired share: share of families whose twin scores lower (more trustworthy) than
  its malicious partner, strictly.

A record is flagged when any of its sentences scores strictly above the threshold, the passage
filter's view (record basis, the primary table); the target basis uses the target sentence alone and
exists only for the twin and the malicious record (the controls have no target sentence). Each
figure is given overall and by attack category, semantic role and cue position, as the mean over
seeds with the seed spread and, overall, the spread over the per-fold values of every seed. The
bag-of-words baseline (bow_baseline_v1.json, the same folds) is the first row; the paired share is
the last column. The released CAD test is a separate table, leak-excluded as evaluation
leak-excluded reports it, for N0, M0 and each round's M1 to M3.
"""

import json
from pathlib import Path

import numpy as np

from rag_cad.data.jsonl import read_jsonl
from rag_cad.operations.paths import local_path
from rag_cad.operations.provenance import sha256, write_json
from rag_cad.training.fold_driver import (
    BREAKDOWN_FIELDS,
    CONDITIONS,
    HELD_RECORDS,
    M0,
    N0,
    RUN_FILE,
    TEST_METRICS,
    cell_complete,
)

SCHEMA = "rag_cad.fold_tables/1"
METRICS = ("twin_false_alarm", "random_control_false_alarm", "keyword_control_false_alarm",
           "malicious_detection", "paired_share")
LABELS = {"twin_false_alarm": "twin FA", "random_control_false_alarm": "random FA",
          "keyword_control_false_alarm": "keyword FA", "malicious_detection": "detection",
          "paired_share": "paired share"}
KIND_METRIC = {"twin": "twin_false_alarm", "random_control": "random_control_false_alarm",
               "keyword_control": "keyword_control_false_alarm", "malicious": "malicious_detection"}
BASES = {"record": ("flagged", "max_probability"), "target": ("target_flagged", "target_probability")}
TEST_HEADLINE = (("masked_average_precision", "upstream_masked", ("average_precision",)),
                 ("masked_tpr", "upstream_masked", ("at_threshold_strict", "tpr")),
                 ("all_rows_average_precision", "all_rows", ("average_precision",)),
                 ("all_rows_tpr", "all_rows", ("at_threshold_strict", "tpr")),
                 ("all_rows_fpr", "all_rows", ("at_threshold_strict", "fpr")))
BOW_BREAKDOWNS = {"semantic_role": "per_role", "attack_category": "per_attack_category",
                  "cue_position": "per_cue_position"}
SEED_NONE = "none"


def _share(values: list[bool]) -> float | None:
    return round(sum(values) / len(values), 6) if values else None


def family_metrics(records: list[dict], basis: str = "record") -> dict:
    """The five figures over a set of held-out records; None where a record kind is absent."""
    flag, score = BASES[basis]
    result = {}
    for kind, metric in KIND_METRIC.items():
        members = [record[flag] for record in records if record["record_kind"] == kind and record[flag] is not None]
        result[metric] = _share(members)
    pairs: dict[str, dict] = {}
    for record in records:
        if record["record_kind"] in ("twin", "malicious") and record[score] is not None:
            pairs.setdefault(record["group_id"], {})[record["record_kind"]] = record[score]
    complete = [pair for pair in pairs.values() if len(pair) == 2]
    result["paired_share"] = _share([pair["twin"] < pair["malicious"] for pair in complete])
    result["families"] = len({record["group_id"] for record in records})
    result["paired_families"] = len(complete)
    return result


def _spread(values: list[float | None]) -> dict:
    present = [value for value in values if value is not None]
    if not present:
        return {"mean": None, "sd": None, "n": 0}
    array = np.asarray(present, dtype=float)
    return {"mean": round(float(array.mean()), 6), "sd": round(float(array.std()), 6), "n": len(present)}


def load_run(run: Path) -> tuple[dict, dict[str, dict]]:
    """The run file and every complete cell manifest, keyed by cell name."""
    run = local_path(run)
    run_file = json.loads((run / RUN_FILE).read_text(encoding="utf-8"))
    cells = {}
    for manifest_path in sorted((run / "cells").rglob("manifest.json")):
        directory = manifest_path.parent
        manifest = cell_complete(directory, run_file["config_fingerprint"])
        if manifest is None:
            raise ValueError(f"Cell {directory.relative_to(run)} is incomplete or altered")
        manifest["directory"] = directory
        cells[manifest["cell"]] = manifest
    if not cells:
        raise ValueError("The run holds no complete cell")
    return run_file, cells


def pooled_records(cells: dict[str, dict], groups: set[str]) -> dict[str, dict[str, list[dict]]]:
    """Held-out records per condition and seed, pooled over rounds; each family exactly once."""
    pooled: dict[str, dict[str, list[dict]]] = {}
    for manifest in cells.values():
        seed = SEED_NONE if manifest["seed"] is None else str(manifest["seed"])
        pooled.setdefault(manifest["condition"], {}).setdefault(seed, []).extend(
            read_jsonl(manifest["directory"] / HELD_RECORDS))
    for condition, seeds in pooled.items():
        for seed, records in seeds.items():
            ids = [record["record_id"] for record in records]
            covered = {record["group_id"] for record in records}
            if len(ids) != len(set(ids)) or covered != groups:
                raise ValueError(f"{condition} seed {seed}: held-out families are not each scored once; "
                                 "the run is partial or overlapping")
    return pooled


def condition_table(seeds: dict[str, list[dict]], basis: str) -> dict:
    per_seed, fold_values, slices = {}, {metric: [] for metric in METRICS}, {}
    for seed, records in sorted(seeds.items()):
        folds = sorted({record["fold"] for record in records})
        per_fold = {str(fold): family_metrics([r for r in records if r["fold"] == fold], basis) for fold in folds}
        for values in per_fold.values():
            for metric in METRICS:
                fold_values[metric].append(values[metric])
        by = {name: {value: family_metrics([r for r in records if r[name] == value], basis)
                     for value in sorted({record[name] for record in records})} for name in BREAKDOWN_FIELDS}
        per_seed[seed] = {"overall": family_metrics(records, basis), "per_fold": per_fold, "by": by}
        for name, values in by.items():
            for value, metrics in values.items():
                slices.setdefault(name, {}).setdefault(value, []).append(metrics)
    overall = {metric: {**_spread([entry["overall"][metric] for entry in per_seed.values()]),
                        "fold_sd": _spread(fold_values[metric])["sd"]} for metric in METRICS}
    by = {name: {value: {metric: _spread([entry[metric] for entry in entries]) for metric in METRICS}
                 for value, entries in values.items()} for name, values in slices.items()}
    families = {entry["overall"]["families"] for entry in per_seed.values()}
    return {"seeds": sorted(per_seed), "families": max(families), "overall": overall, "by": by,
            "per_seed": per_seed}


def bow_row(bow: dict) -> dict:
    """The bag-of-words baseline in the table's terms: a twin it calls malicious is a false alarm."""
    def convert(block: dict) -> dict:
        twin = block.get("twin_accuracy")
        return {"twin_false_alarm": None if twin is None else round(1 - twin, 6),
                "random_control_false_alarm": None, "keyword_control_false_alarm": None,
                "malicious_detection": block.get("malicious_accuracy"), "paired_share": block.get("paired_share")}

    overall = convert(bow["overall"])
    folds = [convert(block) for block in bow["per_fold"].values()]
    return {"seeds": [SEED_NONE], "families": bow["overall"]["families"],
            "overall": {metric: {"mean": overall[metric], "sd": None if overall[metric] is None else 0.0,
                                 "n": 0 if overall[metric] is None else 1,
                                 "fold_sd": _spread([fold[metric] for fold in folds])["sd"]} for metric in METRICS},
            "by": {name: {value: {metric: {"mean": convert(block)[metric], "sd": None, "n": 1}
                                  for metric in METRICS}
                          for value, block in bow[key].items()} for name, key in BOW_BREAKDOWNS.items()},
            "note": "twin vs malicious only, no controls; deterministic, one value per figure"}


def _metric(section: dict, path: tuple[str, ...]):
    for key in path:
        section = section[key]
    return section


def released_test_table(cells: dict[str, dict]) -> dict:
    groups: dict[str, list[dict]] = {}
    for manifest in cells.values():
        name = manifest["condition"] if manifest["round"] is None else f"{manifest['condition']}/round_{manifest['round']}"
        metrics = json.loads((manifest["directory"] / TEST_METRICS).read_text(encoding="utf-8"))
        groups.setdefault(name, []).append(metrics)
        if manifest["round"] is not None:
            groups.setdefault(f"{manifest['condition']}/all_rounds", []).append(metrics)
    table = {}
    for name in sorted(groups, key=_test_order):
        entries = groups[name]
        table[name] = {exclusion: {"rows": entries[0][exclusion]["rows"], **{
            label: _spread([_metric(entry[exclusion][block], path) for entry in entries])
            for label, block, path in TEST_HEADLINE}} for exclusion in entries[0]}
    return table


def _test_order(name: str):
    condition, _, rest = name.partition("/")
    return (CONDITIONS.index(condition), rest == "all_rounds", rest)


def build_tables(run: Path, bow_path: Path) -> dict:
    run_file, cells = load_run(run)
    bow = json.loads(local_path(bow_path).read_text(encoding="utf-8"))
    if bow.get("input", {}).get("folds_sha256") != run_file["config"]["folds_sha256"]:
        raise ValueError("The bag-of-words baseline was computed on another fold table")
    groups = {record["group_id"] for manifest in cells.values()
              for record in read_jsonl(manifest["directory"] / HELD_RECORDS)}
    pooled = pooled_records(cells, groups)
    order = [condition for condition in CONDITIONS if condition in pooled]
    family = {basis: {"bow_baseline": bow_row(bow) if basis == "record" else None,
                      **{condition: condition_table(pooled[condition], basis) for condition in order}}
              for basis in BASES}
    family["target"].pop("bow_baseline")
    timings = [manifest["timings_seconds"] for manifest in cells.values()]
    trained = [timing for timing in timings if timing["train"] > 0]
    return {"schema": SCHEMA, "run": str(local_path(run)), "config_fingerprint": run_file["config_fingerprint"],
            "mode": run_file["config"]["mode"], "trainer": run_file["config"]["trainer"],
            "epochs": run_file["config"]["recipe"]["epochs"], "threshold": run_file["config"]["threshold"],
            "folds_sha256": run_file["config"]["folds_sha256"], "bow_baseline_sha256": sha256(local_path(bow_path)),
            "cells": len(cells), "cells_by_condition": {condition: sum(m["condition"] == condition
                                                                       for m in cells.values()) for condition in order},
            "families": len(groups),
            "cell_seconds": {"trained_cells": len(trained),
                             "mean_train": _spread([timing["train"] for timing in trained])["mean"],
                             "mean_total": _spread([timing["total"] for timing in timings])["mean"],
                             "max_total": round(max(timing["total"] for timing in timings), 3)},
            "definitions": {"record_basis": "a record is flagged when any sentence scores strictly above the "
                                            "threshold; paired share compares the records' maximum probabilities",
                            "target_basis": "the target sentence alone; twin and malicious records only",
                            "paired_share": "share of families whose twin scores strictly lower (more "
                                            "trustworthy) than its malicious partner",
                            "spread": "mean over seeds; sd is the population sd over seeds; fold_sd is the "
                                      "population sd over the per-fold values of every seed",
                            "released_test": "leak-excluded as evaluation leak-excluded: full, minus_verbatim, "
                                             "minus_near; mean and sd over seeds"},
            "family_tables": family, "released_test": released_test_table(cells)}


def _cell(entry: dict | None, *, fold: bool = True) -> str:
    if entry is None or entry.get("mean") is None:
        return "n/a"
    text = f"{entry['mean']:.3f}"
    if entry.get("n", 0) > 1:
        text += f" ± {entry['sd']:.3f}"
    if fold and entry.get("fold_sd") is not None:
        text += f" (f {entry['fold_sd']:.3f})"
    return text


NAMES = {"bow_baseline": "BoW baseline", N0: "N0 released", M0: "M0 base", "m1_random": "M1 random",
         "m2_keyword": "M2 keyword", "m3_semantic": "M3 semantic"}


def markdown(tables: dict) -> str:
    lines = [f"# Fold tables ({tables['mode']}, {tables['trainer']} trainer, {tables['epochs']} epochs)", "",
             f"Cells: {tables['cells']}; families: {tables['families']}; config {tables['config_fingerprint'][:12]}.",
             "Values are the mean over seeds, ± the seed sd when there is more than one seed, and (f ...) the "
             "sd over the per-fold values. A record is flagged when any sentence scores above the threshold.", ""]
    def overall(basis: str, metrics=METRICS):
        lines.extend(["| row | " + " | ".join(LABELS[metric] for metric in metrics) + " |",
                      "|" + "---|" * (len(metrics) + 1)])
        for name, table in tables["family_tables"][basis].items():
            lines.append(f"| {NAMES[name]} | " + " | ".join(_cell(table["overall"][m]) for m in metrics) + " |")
        lines.append("")

    lines.append("## Held-out families, pooled over rounds (record basis)")
    lines.append("")
    overall("record")
    for name in BREAKDOWN_FIELDS:
        lines.extend([f"### By {name.replace('_', ' ')}", "", "| slice | row | " +
                      " | ".join(LABELS[metric] for metric in METRICS) + " |", "|" + "---|" * (len(METRICS) + 2)])
        values = sorted({value for table in tables["family_tables"]["record"].values() for value in table["by"][name]})
        for value in values:
            for row, table in tables["family_tables"]["record"].items():
                entry = table["by"][name].get(value)
                if entry is not None:
                    lines.append(f"| {value} | {NAMES[row]} | " +
                                 " | ".join(_cell(entry[m], fold=False) for m in METRICS) + " |")
        lines.append("")
    lines.extend(["## Held-out families, target sentence basis (twin and malicious only)", ""])
    overall("target", ("twin_false_alarm", "malicious_detection", "paired_share"))
    lines.extend(["## Released CAD test", "",
                  "Leak-excluded (minus_near: test records whose malicious sentences are verbatim or near "
                  "duplicates of D0 training sentences removed) beside the full set; strict threshold.", "",
                  "| row | set | rows | masked AP | masked TPR | all-rows AP | all-rows TPR | all-rows FPR |",
                  "|---|---|---|---|---|---|---|---|"])
    for name, entry in tables["released_test"].items():
        for exclusion in ("minus_near", "full"):
            section = entry[exclusion]
            lines.append(f"| {name} | {exclusion} | {section['rows']} | " + " | ".join(
                _cell(section[label], fold=False) for label, _, _ in TEST_HEADLINE) + " |")
    return "\n".join(lines) + "\n"


def fold_tables_command(args) -> dict:
    for path in (args.run, args.bow, args.output, args.markdown):
        local_path(path)
    tables = build_tables(args.run, args.bow)
    write_json(args.output, tables)
    with local_path(args.markdown).open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(markdown(tables))
    return {key: tables[key] for key in ("schema", "mode", "trainer", "epochs", "cells", "cells_by_condition",
                                          "families", "cell_seconds")} | {"output": str(args.output),
                                                                          "markdown": str(args.markdown)}
