"""Five-fold assignment of the semantic-pair families and the leakage check per round.

D-20261013-28 (with its amendment) and D-20261017-51: folds are cut at the family level
(group_id), seed 764, stratified by semantic role and, within role, balanced by attack
category; in round k the families of fold k are held out with all four of their records.
"""

from collections import Counter, defaultdict

from rag_cad.data.schema import ContractError, dataset_digest
from rag_cad.data.similarity import normalise
from rag_cad.data.split import MANIFEST_SCHEMA, check_leakage, order_key
from rag_cad.data.validate import EXAMPLE_LIMIT, unique_records

FOLDS_SCHEMA = "rag_cad.folds/1"
FOLD_COUNT = 5
ATTACK_CATEGORIES = {"bipia_adapted": "task_type", "asb_adapted": "operational"}
FOLD_FIELDS = ("family_id", "group_id", "fold", "semantic_role", "attack_category", "cue_position")


def family_table(records, manifest_entries) -> list[dict]:
    """One row per family: role and cue position from the manifest, attack category from the
    malicious record's source (BIPIA task-type string or ASB operational instruction)."""
    checked = unique_records(records)
    malicious = defaultdict(list)
    groups = defaultdict(set)
    for record in checked:
        if record["family_id"] is not None:
            groups[record["family_id"]].add(record["group_id"])
            if record["condition_source"] == "shared_malicious":
                malicious[record["family_id"]].append(record)
    entries = {}
    for entry in manifest_entries:
        family = entry.get("family_id")
        if family in entries:
            raise ValueError(f"Family listed twice in the manifest: {family}")
        entries[family] = entry
    if set(entries) != set(groups):
        missing = sorted(set(groups) ^ set(entries))
        raise ValueError(f"Manifest and records name different families: {missing[:EXAMPLE_LIMIT]}")
    rows = []
    for family in sorted(entries):
        entry = entries[family]
        if groups[family] != {entry["group_id"]}:
            raise ValueError(f"Manifest group differs from the records: {family}")
        if len(malicious[family]) != 1:
            raise ValueError(f"Family needs exactly one malicious record: {family}")
        source = malicious[family][0]["provenance"]["source_dataset"]
        if source not in ATTACK_CATEGORIES:
            raise ValueError(f"Malicious record has no attack category: {family}")
        rows.append({"family_id": family, "group_id": entry["group_id"],
                     "semantic_role": entry["semantic_role"],
                     "attack_category": ATTACK_CATEGORIES[source],
                     "cue_position": entry["cue_position"]})
    return rows


SEARCH_LIMIT = 5 ** 9  # memory is about combinations x folds x columns x 12 bytes


def _spread(values) -> int:
    return max(values) - min(values)


def _ordered(members, seed: int) -> list[dict]:
    return sorted(members, key=lambda row: (row["attack_category"], row["cue_position"],
                                            order_key(seed, row["group_id"]), row["group_id"]))


def best_starts(ordered: dict[str, list[dict]], folds: int) -> dict[str, int]:
    """Exhaustive choice of each role's starting fold (0-based): minimise the sum of squared
    attack-category totals per fold, then the sum of squared cue-position totals per fold;
    ties go to the lexicographically smallest tuple of starts over roles in name order."""
    import numpy as np

    roles = sorted(ordered)
    if folds ** len(roles) > SEARCH_LIMIT:
        raise ValueError("Too many roles for the exhaustive start search")
    categories = sorted({row["attack_category"] for rows in ordered.values() for row in rows})
    cues = sorted({row["cue_position"] for rows in ordered.values() for row in rows})
    columns = {("c", key): index for index, key in enumerate(categories)}
    columns.update({("p", key): len(categories) + index for index, key in enumerate(cues)})
    contribution = np.zeros((len(roles), folds, folds, len(columns)), dtype=np.int32)
    for role_index, role in enumerate(roles):
        for start in range(folds):
            for index, row in enumerate(ordered[role]):
                fold = (start + index) % folds
                contribution[role_index, start, fold, columns[("c", row["attack_category"])]] += 1
                contribution[role_index, start, fold, columns[("p", row["cue_position"])]] += 1
    combos = np.indices((folds,) * len(roles)).reshape(len(roles), -1).T
    totals = np.zeros((len(combos), folds, len(columns)), dtype=np.int32)
    for role_index in range(len(roles)):
        totals += contribution[role_index][combos[:, role_index]]
    squares = totals.astype(np.int64) ** 2
    category_cost = squares[:, :, :len(categories)].sum(axis=(1, 2))
    cue_cost = squares[:, :, len(categories):].sum(axis=(1, 2))
    best = int(np.lexsort((cue_cost, category_cost))[0])
    return {role: int(combos[best, index]) for index, role in enumerate(roles)}


def assign_folds(records, manifest_entries, seed: int, folds: int = FOLD_COUNT) -> tuple[list[dict], dict]:
    """Deterministic stratified assignment; returns the fold rows (folds numbered 1..folds) and a summary.

    Within each role the families are ordered by attack category, then cue position, then the
    seeded hash of their group_id, and dealt round robin from a per-role starting fold. Any
    run of consecutive families therefore lands in distinct folds, so every fold receives
    floor or ceil of n/folds of each role and of each category within the role. The starting
    folds are then chosen by exhaustive search (best_starts) to balance the attack-category
    totals over folds first and the cue-position totals second.
    """
    if isinstance(seed, bool) or type(seed) is not int or seed < 0:
        raise ValueError("Fold seed must be a non-negative integer")
    if isinstance(folds, bool) or type(folds) is not int or folds < 2:
        raise ValueError("Fold count must be an integer of at least two")
    table = family_table(records, manifest_entries)
    by_role = defaultdict(list)
    for row in table:
        by_role[row["semantic_role"]].append(row)
    ordered = {role: _ordered(members, seed) for role, members in by_role.items()}
    starts = best_starts(ordered, folds)
    fold_of = {row["family_id"]: (starts[role] + index) % folds + 1
               for role, members in ordered.items() for index, row in enumerate(members)}
    rows = [{field: ({**row, "fold": fold_of[row["family_id"]]})[field] for field in FOLD_FIELDS}
            for row in table]
    summary = {"schema": FOLDS_SCHEMA, "seed": seed, "folds": folds, "group_field": "group_id",
               "stratified_by": ["semantic_role", "attack_category"],
               "attack_categories": ATTACK_CATEGORIES,
               "role_start_fold": {role: start + 1 for role, start in sorted(starts.items())},
               "input": {"records": len(records), "families": len(rows),
                         "content_sha256": dataset_digest(unique_records(records))},
               **fold_counts(rows, folds)}
    return rows, summary


def fold_counts(rows, folds: int = FOLD_COUNT) -> dict:
    """Achieved counts per fold by role, category, role and category, and cue position, with the
    worst cell of each axis (the largest spread between folds)."""
    names = [str(fold) for fold in range(1, folds + 1)]

    def table(*fields):
        counts = {name: Counter() for name in names}
        for row in rows:
            counts[str(row["fold"])][" / ".join(row[field] for field in fields)] += 1
        keys = sorted({key for count in counts.values() for key in count})
        return {name: {key: counts[name][key] for key in keys} for name in names}, keys

    result, worst = {}, {}
    for label, fields in (("by_role", ("semantic_role",)), ("by_category", ("attack_category",)),
                          ("by_role_category", ("semantic_role", "attack_category")),
                          ("by_cue_position", ("cue_position",))):
        counts, keys = table(*fields)
        result[label] = counts
        spreads = {key: _spread([counts[name][key] for name in names]) for key in keys}
        top = max(spreads.values()) if spreads else 0
        worst[label] = {"max_spread_between_folds": top,
                        "cells": sorted(key for key, value in spreads.items() if value == top)}
    result["families_per_fold"] = {name: sum(1 for row in rows if str(row["fold"]) == name) for name in names}
    result["balance"] = worst
    return result


def validate_folds(rows, folds: int = FOLD_COUNT) -> dict[str, dict]:
    """Check a folds_v1.jsonl table and return it keyed by family_id."""
    keyed, groups = {}, {}
    for row in rows:
        if set(row) != set(FOLD_FIELDS):
            raise ValueError("Fold rows must carry exactly the fold fields")
        if row["family_id"] in keyed:
            raise ValueError(f"Family assigned twice: {row['family_id']}")
        fold = row["fold"]
        if isinstance(fold, bool) or type(fold) is not int or not 1 <= fold <= folds:
            raise ValueError(f"Invalid fold for {row['family_id']}")
        if groups.setdefault(row["group_id"], fold) != fold:
            raise ValueError(f"Group split across folds: {row['group_id']}")
        keyed[row["family_id"]] = row
    if not keyed:
        raise ValueError("Fold table is empty")
    return keyed


def round_manifest(records, fold_rows, round_number: int) -> dict:
    """The split manifest of one round: the held-out fold is test, every other fold is train."""
    keyed = validate_folds(fold_rows)
    if isinstance(round_number, bool) or type(round_number) is not int \
            or round_number not in {row["fold"] for row in keyed.values()}:
        raise ValueError("Round must name a fold of the table")
    checked = unique_records(records)
    fold_of_group = {row["group_id"]: row["fold"] for row in keyed.values()}
    record_groups = {record["group_id"] for record in checked}
    if record_groups != set(fold_of_group):
        raise ValueError("Fold table and records cover different groups")
    assignments = {group: "test" if fold == round_number else "train"
                   for group, fold in sorted(fold_of_group.items())}
    return {"schema": MANIFEST_SCHEMA, "group_field": "group_id", "seed": None, "round": round_number,
            "input": {"records": len(checked), "groups": len(assignments),
                      "content_sha256": dataset_digest(checked)},
            "assignments": assignments}


def _shared(train, held_out, value) -> list:
    left = set().union(*(value(record) for record in train)) if train else set()
    right = set().union(*(value(record) for record in held_out)) if held_out else set()
    return sorted(left & right)


def cut_overlap(records, manifest: dict) -> dict:
    """Families, record ids, queries and sentence texts (normalised, any kind) on both sides of the cut."""
    split = {record["record_id"]: manifest["assignments"][record["group_id"]] for record in records}
    train = [record for record in records if split[record["record_id"]] == "train"]
    held_out = [record for record in records if split[record["record_id"]] == "test"]
    return {"shared_families": _shared(train, held_out, lambda r: {r["family_id"]} - {None}),
            "shared_record_ids": _shared(train, held_out, lambda r: {r["record_id"]}),
            "shared_queries": _shared(train, held_out, lambda r: {normalise(r["query"])}),
            "shared_sentence_texts": _shared(train, held_out,
                                             lambda r: {normalise(s["text"]) for s in r["sentences"]})}


def check_round(records, fold_rows, round_number: int, *, near_duplicate_threshold: float) -> dict:
    """The existing leakage check on one round's cut plus the exact-overlap check of D-20261017-51 (b).

    Raises ContractError carrying the report when anything crosses the cut."""
    checked = unique_records(records)
    manifest = round_manifest(checked, fold_rows, round_number)
    try:
        report = check_leakage(checked, manifest, near_duplicate_threshold=near_duplicate_threshold)
    except ContractError as error:
        report = error.report
    overlap = cut_overlap(checked, manifest)
    held_out = sorted(row["family_id"] for row in fold_rows if row["fold"] == round_number)
    report = {"round": round_number, "held_out_fold": round_number, "held_out_families": len(held_out),
              "training_families": len(fold_rows) - len(held_out), **report,
              "cut_overlap_counts": {key: len(value) for key, value in overlap.items()},
              "cut_overlap": {key: value[:EXAMPLE_LIMIT] for key, value in overlap.items()}}
    report["leakage_free"] = report["leakage_free"] and not any(report["cut_overlap_counts"].values())
    if not report["leakage_free"]:
        raise ContractError(f"Leakage detected in round {round_number}", report)
    return report
