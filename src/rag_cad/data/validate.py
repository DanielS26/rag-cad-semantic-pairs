"""Dataset-level contracts: identities, families, segmentation round trip, duplicate diagnostics."""

from collections import Counter, defaultdict

from rag_cad.cad.upstream_adapter import split_units
from rag_cad.data.schema import dataset_digest, passage, texts, validate_record
from rag_cad.data.similarity import (
    exact_duplicates,
    near_duplicates,
    near_duplicates_against,
    normalise,
)

EXAMPLE_LIMIT = 20


def unique_records(records, *, require_split: bool = False) -> list[dict]:
    checked = [validate_record(record, require_split=require_split) for record in records]
    counts = Counter(record["record_id"] for record in checked)
    repeated = sorted(record_id for record_id, count in counts.items() if count > 1)
    if repeated:
        raise ValueError(f"Duplicate record_id values: {repeated[:EXAMPLE_LIMIT]}")
    return checked


def family_groups(records) -> dict[str, str]:
    """Every family must live inside exactly one leakage group."""
    groups = defaultdict(set)
    for record in records:
        if record["family_id"] is not None:
            groups[record["family_id"]].add(record["group_id"])
    spanning = sorted(family for family, members in groups.items() if len(members) > 1)
    if spanning:
        raise ValueError(f"Families span more than one group: {spanning[:EXAMPLE_LIMIT]}")
    return {family: next(iter(members)) for family, members in groups.items()}


def check_families(records) -> dict:
    members = defaultdict(list)
    for record in records:
        if record["family_id"] is not None:
            members[record["family_id"]].append(record)
    incomplete, differing = [], []
    for family, items in sorted(members.items()):
        kinds = {item["pair_member"] for item in items}
        if kinds != {"benign", "malicious"}:
            incomplete.append(family)
            continue
        targets = {kind: {normalise(sentence["text"]) for item in items if item["pair_member"] == kind
                          for sentence in item["sentences"] if sentence["is_target"]}
                   for kind in kinds}
        if targets["benign"] != targets["malicious"]:
            differing.append(family)
    if incomplete:
        raise ValueError(f"Families lack a benign and a malicious member: {incomplete[:EXAMPLE_LIMIT]}")
    return {"families": len(members), "families_with_differing_targets": differing}


def roundtrip_failures(records, tokenize) -> list[str]:
    """Records whose newline-joined passage does not re-segment to the canonical list."""
    return [record["record_id"] for record in records
            if split_units(passage(record), tokenize) != texts(record)]


def sentence_kind(sentence: dict) -> str:
    return "target_or_malicious" if sentence["is_target"] or sentence["label"] else "benign_context"


def record_items(records) -> list[tuple[str, str]]:
    return [(record["record_id"], record["query"] + "\n" + passage(record)) for record in records]


def sentence_items(records, *, kind: str | None = None) -> list[tuple[tuple[str, int], str]]:
    return [((record["record_id"], sentence["sentence_id"]), sentence["text"])
            for record in records for sentence in record["sentences"]
            if kind is None or sentence_kind(sentence) == kind]


def record_of(key) -> str:
    return key[0] if isinstance(key, tuple) else key


def as_json(key):
    return list(key) if isinstance(key, tuple) else key


def examples(pairs) -> list:
    return [[as_json(left), as_json(right), round(similarity, 4)]
            for left, right, similarity in pairs[:EXAMPLE_LIMIT]]


def crossing_duplicates(by_id: dict, items, field: str) -> dict[str, list]:
    """Exact duplicate groups spanning several values of a record field, split by sentence kind."""
    found = {"target_or_malicious": [], "benign_context": []}
    for keys in exact_duplicates(items).values():
        if len({by_id[record_of(key)][field] for key in keys}) > 1:
            kinds = {sentence_kind(by_id[key[0]]["sentences"][key[1]]) for key in keys}
            kind = "target_or_malicious" if "target_or_malicious" in kinds else "benign_context"
            found[kind].append([as_json(key) for key in sorted(keys)])
    return found


def target_near_duplicates(records, threshold: float, related) -> list[tuple]:
    """Every target or malicious sentence compared against every sentence of any kind."""
    return near_duplicates_against(sentence_items(records, kind="target_or_malicious"),
                                   sentence_items(records), threshold, related=related)


def duplicate_diagnostics(records, *, near_duplicate_threshold=None) -> dict:
    """Exact duplicates anywhere plus cross-group duplicates, which signal grouping gaps."""
    by_id = {record["record_id"]: record for record in records}
    exact_records = sorted(sorted(keys) for keys in exact_duplicates(record_items(records)).values())
    cross_group = crossing_duplicates(by_id, sentence_items(records), "group_id")
    report = {"exact_duplicate_records": exact_records,
              "cross_group_exact_sentences": {kind: {"count": len(items), "examples": items[:EXAMPLE_LIMIT]}
                                              for kind, items in cross_group.items()},
              "near_duplicate_threshold": near_duplicate_threshold}
    if near_duplicate_threshold is not None:
        def other_group(left, right):
            return by_id[record_of(left)]["group_id"] != by_id[record_of(right)]["group_id"]

        near_records = near_duplicates(record_items(records), near_duplicate_threshold, related=other_group)
        near_targets = target_near_duplicates(records, near_duplicate_threshold, other_group)
        report["cross_group_near_records"] = {"count": len(near_records), "examples": examples(near_records)}
        report["cross_group_near_target_sentences"] = {"count": len(near_targets),
                                                       "examples": examples(near_targets)}
    return report


def validate_dataset(records, *, tokenize=None, near_duplicate_threshold=None,
                     require_split: bool = False) -> dict:
    from rag_cad.data.conditions import summarise

    checked = unique_records(records, require_split=require_split)
    family_groups(checked)
    families = check_families(checked)
    if tokenize is not None:
        failures = roundtrip_failures(checked, tokenize)
        if failures:
            raise ValueError(f"Segmentation round trip failed for {len(failures)} records: "
                             f"{failures[:EXAMPLE_LIMIT]}")
    diagnostics = duplicate_diagnostics(checked, near_duplicate_threshold=near_duplicate_threshold)
    if diagnostics["exact_duplicate_records"]:
        raise ValueError(f"Exact duplicate records: {diagnostics['exact_duplicate_records'][:EXAMPLE_LIMIT]}")
    return {"records": len(checked), "content_sha256": dataset_digest(checked),
            "roundtrip": "passed" if tokenize is not None else "not_checked",
            **families, "summary": summarise(checked), "diagnostics": diagnostics}
