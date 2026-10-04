"""Deterministic group-level splitting and leakage checks (handoff Section 4.4)."""

import hashlib
from collections import defaultdict

from rag_cad.data.schema import SPLITS, ContractError, dataset_digest, validate_record
from rag_cad.data.similarity import exact_duplicates, near_duplicates
from rag_cad.data.validate import (
    EXAMPLE_LIMIT,
    crossing_duplicates,
    examples,
    family_groups,
    record_items,
    record_of,
    sentence_items,
    target_near_duplicates,
    unique_records,
)

MANIFEST_SCHEMA = "rag_cad.split_manifest/1"


def validate_ratios(ratios) -> dict:
    if not isinstance(ratios, dict) or set(ratios) != set(SPLITS):
        raise ValueError("Split ratios must name exactly train, validation and test")
    values = {}
    for name in SPLITS:
        value = ratios[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1:
            raise ValueError("Split ratios must be numbers between 0 and 1")
        values[name] = float(value)
    if abs(sum(values.values()) - 1) > 1e-9:
        raise ValueError("Split ratios must sum to one")
    if values["train"] <= 0 or values["test"] <= 0:
        raise ValueError("Train and test ratios must be positive")
    return values


D0_SOURCES = ("cad_original_train", "cad_paraphrased_train")
D0_HOLDOUT_POLICIES = ("none",)


def pinned_split(record: dict) -> str | None:
    """Splits that the contract fixes regardless of the seeded assignment: released CAD test
    records are test; official D0 records and their paraphrases are train under the "none"
    holdout policy of D-20261004-15."""
    source = record["provenance"]["source_dataset"]
    if source == "cad_original_test" or record["condition_source"] == "test_only":
        return "test"
    if source in D0_SOURCES:
        return "train"
    return record["split"]


def group_pins(records) -> dict[str, str | None]:
    pins = defaultdict(set)
    for record in records:
        pins[record["group_id"]].add(pinned_split(record))
    result = {}
    for group, values in pins.items():
        declared = values - {None}
        if len(declared) > 1:
            raise ValueError(f"Group has conflicting split assignments: {group}")
        result[group] = next(iter(declared)) if declared else None
    return result


def order_key(seed: int, group_id: str) -> str:
    return hashlib.sha256(f"{seed}\n{group_id}".encode()).hexdigest()


def split_counts(records) -> dict:
    counts = {}
    for name in SPLITS:
        members = [record for record in records if record["split"] == name]
        sentences = [sentence for record in members for sentence in record["sentences"]]
        counts[name] = {"groups": len({record["group_id"] for record in members}),
                        "families": len({record["family_id"] for record in members
                                         if record["family_id"] is not None}),
                        "records": len(members), "sentence_rows": len(sentences),
                        "malicious_rows": sum(sentence["label"] for sentence in sentences),
                        "benign_rows": sum(1 - sentence["label"] for sentence in sentences)}
    return counts


def assign_splits(records, ratios, seed, *, d0_holdout_policy: str = "none") -> dict:
    """Assign every group to one split: pinned groups first, then seeded-hash order by deficit."""
    if isinstance(seed, bool) or type(seed) is not int or seed < 0:
        raise ValueError("Split seed must be a non-negative integer")
    if d0_holdout_policy not in D0_HOLDOUT_POLICIES:
        raise ValueError("Only the none D0 holdout policy is implemented (D-20261004-15)")
    ratios = validate_ratios(ratios)
    checked = unique_records(records)
    family_groups(checked)
    pins = group_pins(checked)
    assignments = {group: split for group, split in pins.items() if split is not None}
    counts = {name: sum(1 for split in assignments.values() if split == name) for name in SPLITS}
    total = len(pins)
    candidates = [name for name in SPLITS if ratios[name] > 0]
    pending = sorted((group for group, split in pins.items() if split is None),
                     key=lambda group: (order_key(seed, group), group))
    for group in pending:
        chosen = max(candidates, key=lambda name: (ratios[name] * total - counts[name],
                                                   -SPLITS.index(name)))
        assignments[group] = chosen
        counts[chosen] += 1
    assigned = [{**record, "split": assignments[record["group_id"]]} for record in checked]
    return {"schema": MANIFEST_SCHEMA, "group_field": "group_id", "seed": seed, "ratios": ratios,
            "d0_holdout_policy": d0_holdout_policy,
            "input": {"records": len(checked), "groups": total, "content_sha256": dataset_digest(checked)},
            "pinned_groups": sorted(group for group, split in pins.items() if split is not None),
            "assignments": dict(sorted(assignments.items())), "counts": split_counts(assigned)}


def apply_manifest(records, manifest: dict) -> list[dict]:
    """Fill every record's split from the manifest, refusing drift or contradictions."""
    checked = unique_records(records)
    if not isinstance(manifest, dict) or manifest.get("schema") != MANIFEST_SCHEMA \
            or manifest.get("group_field") != "group_id":
        raise ValueError("Unknown split manifest")
    if manifest["input"]["content_sha256"] != dataset_digest(checked):
        raise ValueError("Records changed since the split manifest was created")
    assignments = manifest["assignments"]
    result = []
    for record in checked:
        split = assignments.get(record["group_id"])
        if split not in SPLITS:
            raise ValueError(f"Group missing from split manifest: {record['group_id']}")
        pinned = pinned_split(record)
        if pinned is not None and pinned != split:
            raise ValueError(f"Manifest contradicts a fixed split [{record['record_id']}]")
        result.append(validate_record({**record, "split": split}))
    return result


def check_leakage(records, manifest: dict, *, near_duplicate_threshold: float) -> dict:
    """Raise ContractError (with its report) when any family, group, record or target crosses splits."""
    assigned = apply_manifest(records, manifest)
    by_id = {record["record_id"]: record for record in assigned}
    group_splits, family_splits = defaultdict(set), defaultdict(set)
    for record in assigned:
        group_splits[record["group_id"]].add(record["split"])
        if record["family_id"] is not None:
            family_splits[record["family_id"]].add(record["split"])
    test_families = {family for family, splits in family_splits.items() if "test" in splits}
    seen_families = {family for family, splits in family_splits.items() if splits & {"train", "validation"}}

    def other_split(left, right):
        return by_id[record_of(left)]["split"] != by_id[record_of(right)]["split"]

    records_text = record_items(assigned)
    exact_records = [sorted(keys) for keys in exact_duplicates(records_text).values()
                     if len({by_id[key]["split"] for key in keys}) > 1]
    sentences = crossing_duplicates(by_id, sentence_items(assigned), "split")
    near_records = near_duplicates(records_text, near_duplicate_threshold, related=other_split)
    near_targets = target_near_duplicates(assigned, near_duplicate_threshold, other_split)
    errors = {"groups_across_splits": sorted(g for g, s in group_splits.items() if len(s) > 1),
              "families_across_splits": sorted(f for f, s in family_splits.items() if len(s) > 1),
              "test_families_seen_in_training": sorted(test_families & seen_families),
              "exact_duplicate_records_across_splits": exact_records,
              "near_duplicate_records_across_splits": examples(near_records),
              "exact_target_sentences_across_splits": sentences["target_or_malicious"],
              "near_target_sentences_across_splits": examples(near_targets)}
    counts = {key: len(value) for key, value in errors.items()}
    counts["near_duplicate_records_across_splits"] = len(near_records)
    counts["near_target_sentences_across_splits"] = len(near_targets)
    report = {"records": len(assigned), "manifest_content_sha256": manifest["input"]["content_sha256"],
              "near_duplicate_threshold": near_duplicate_threshold, "counts": split_counts(assigned),
              "error_counts": counts, "errors": {key: value[:EXAMPLE_LIMIT] for key, value in errors.items()},
              "benign_context_sentence_overlap": {"count": len(sentences["benign_context"]),
                                                  "examples": sentences["benign_context"][:EXAMPLE_LIMIT]},
              "leakage_free": not any(counts.values())}
    if not report["leakage_free"]:
        raise ContractError(f"Leakage detected: {counts}", report)
    return report


def training_records(records, manifest: dict, condition_id: str) -> list[dict]:
    """The only sanctioned way to select training rows: never validation, test or released test data."""
    from rag_cad.data.conditions import select

    selected = select(apply_manifest(records, manifest), condition_id, split="train")
    forbidden = sorted(record["record_id"] for record in selected
                       if record["split"] != "train" or record["condition_source"] == "test_only"
                       or record["provenance"]["source_dataset"] == "cad_original_test")
    if forbidden:
        raise ValueError(f"Training selection would include held-out records: {forbidden[:EXAMPLE_LIMIT]}")
    return selected
