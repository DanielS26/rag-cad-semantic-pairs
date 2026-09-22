"""Condition composition and equal-budget accounting (handoff Sections 4.2 and 4.3)."""

from collections import Counter, defaultdict

from rag_cad.data.schema import CONDITION_SOURCES, SPLITS, ContractError

CONDITIONS = {"m0_base": ("base",),
              "m1_random": ("base", "shared_malicious", "random_benign"),
              "m2_keyword": ("base", "shared_malicious", "keyword_benign"),
              "m3_semantic": ("base", "shared_malicious", "semantic_benign")}
PRIMARY = ("m1_random", "m2_keyword", "m3_semantic")
BENIGN_CONTROLS = ("random_benign", "keyword_benign", "semantic_benign")
UNIT_SOURCES = ("shared_malicious",) + BENIGN_CONTROLS
COUNT_KEYS = ("records", "sentence_rows", "malicious_rows", "benign_rows")


def select(records, condition_id: str, *, split: str = "train") -> list[dict]:
    if condition_id not in CONDITIONS:
        raise ValueError("Unknown condition")
    if split not in SPLITS:
        raise ValueError("Unknown split")
    chosen = []
    for record in records:
        if record["split"] is None:
            raise ValueError("Condition selection requires assigned splits")
        if record["split"] == split and record["condition_source"] in CONDITIONS[condition_id]:
            chosen.append(record)
    return chosen


def _counts(records) -> dict:
    sentences = [sentence for record in records for sentence in record["sentences"]]
    malicious = sum(sentence["label"] for sentence in sentences)
    return {"records": len(records), "sentence_rows": len(sentences), "malicious_rows": malicious,
            "benign_rows": len(sentences) - malicious,
            "target_rows": sum(sentence["is_target"] for sentence in sentences),
            "characters": sum(len(sentence["text"]) for sentence in sentences)}


def summarise(records) -> dict:
    """Document-level and sentence-level totals with breakdowns; no research meaning by itself."""
    records = list(records)
    totals = _counts(records)
    sentences = [sentence for record in records for sentence in record["sentences"]]
    return {**totals,
            "groups": len({record["group_id"] for record in records}),
            "families": len({record["family_id"] for record in records if record["family_id"] is not None}),
            "mean_sentences_per_record": round(len(sentences) / len(records), 4) if records else 0.0,
            "mean_characters_per_sentence": round(totals["characters"] / len(sentences), 4) if sentences else 0.0,
            "by_source": {source: _counts([r for r in records if r["condition_source"] == source])
                          for source in CONDITION_SOURCES
                          if any(r["condition_source"] == source for r in records)},
            "by_split": dict(sorted(Counter(str(record["split"]) for record in records).items())),
            "by_domain": dict(sorted(Counter(record["domain"] for record in records).items())),
            "by_semantic_role": dict(sorted(Counter(sentence["semantic_role"] for sentence in sentences
                                                    if sentence["semantic_role"] is not None).items()))}


def compare_budgets(records, condition_ids=PRIMARY, *, split: str = "train",
                    length_tolerance: float | None = None) -> dict:
    """Refuse unless the conditions differ only in their benign half at equal sentence budgets."""
    condition_ids = tuple(condition_ids)
    if len(condition_ids) < 2 or len(set(condition_ids)) != len(condition_ids):
        raise ValueError("At least two distinct conditions are required")
    if length_tolerance is not None and (isinstance(length_tolerance, bool)
                                         or not isinstance(length_tolerance, (int, float))
                                         or length_tolerance < 0):
        raise ValueError("Length tolerance must be a non-negative number or null")
    selections = {condition: select(records, condition, split=split) for condition in condition_ids}
    summaries = {condition: summarise(selection) for condition, selection in selections.items()}
    mismatches = {key: {condition: summaries[condition][key] for condition in condition_ids}
                  for key in COUNT_KEYS if len({summaries[c][key] for c in condition_ids}) > 1}
    shared = {condition: sorted(record["record_id"] for record in selection
                                if record["condition_source"] in ("base", "shared_malicious"))
              for condition, selection in selections.items()}
    shared_pools_identical = len({tuple(ids) for ids in shared.values()}) == 1
    units = defaultdict(lambda: defaultdict(list))
    for record in records:
        if record["split"] == split and record["condition_source"] in UNIT_SOURCES:
            units[record["group_id"]][record["condition_source"]].append(record)
    incomplete, unequal, ratios = [], [], {}
    for group, variants in sorted(units.items()):
        if set(variants) != set(UNIT_SOURCES):
            incomplete.append(group)
            continue
        counts = {source: sum(len(record["sentences"]) for record in variants[source])
                  for source in BENIGN_CONTROLS}
        if len(set(counts.values())) > 1:
            unequal.append(group)
        characters = {source: sum(len(sentence["text"]) for record in variants[source]
                                  for sentence in record["sentences"]) for source in BENIGN_CONTROLS}
        ratios[group] = round(max(characters.values()) / min(characters.values()), 4)
    worst = max(ratios.values(), default=1.0)
    errors = []
    if mismatches:
        errors.append("condition_counts_differ")
    if not shared_pools_identical:
        errors.append("shared_pools_differ")
    if incomplete:
        errors.append("incomplete_augmentation_units")
    if unequal:
        errors.append("unequal_unit_sentence_counts")
    if length_tolerance is not None and worst > 1 + length_tolerance:
        errors.append("unit_length_ratio_exceeds_tolerance")
    report = {"split": split, "conditions": list(condition_ids), "summaries": summaries,
              "count_mismatches": mismatches, "shared_pools_identical": shared_pools_identical,
              "augmentation_units": len(units), "incomplete_units": incomplete[:50],
              "unequal_sentence_count_units": unequal[:50],
              "unit_character_ratio": {"worst": worst, "tolerance": length_tolerance,
                                       "enforced": length_tolerance is not None},
              "errors": errors, "equal_budget": not errors}
    if errors:
        raise ContractError(f"Budget comparison failed: {errors}", report)
    return report
