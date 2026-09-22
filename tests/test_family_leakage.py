import random
from copy import deepcopy
from pathlib import Path

import pytest

from rag_cad.data.jsonl import read_jsonl
from rag_cad.data.schema import ContractError
from rag_cad.data.split import apply_manifest, assign_splits, check_leakage, training_records
from rag_cad.data.validate import validate_dataset

FIXTURE = Path(__file__).resolve().parents[1] / "tests/fixtures/phase2_families.jsonl"
RATIOS = {"train": 0.6, "validation": 0.2, "test": 0.2}
THRESHOLD = 0.6


def records():
    return read_jsonl(FIXTURE)


def by_split(manifest, split):
    return sorted(group for group, value in manifest["assignments"].items() if value == split)


def member(items, group, source):
    return next(record for record in items if record["group_id"] == group
                and record["condition_source"] == source)


def test_split_is_deterministic_for_seed_764_and_atomic_per_group():
    manifest = assign_splits(records(), RATIOS, 764)
    shuffled = records()
    random.Random(1).shuffle(shuffled)
    assert assign_splits(shuffled, RATIOS, 764) == manifest
    assert {split: manifest["counts"][split]["groups"] for split in RATIOS} == {
        "train": 6, "validation": 2, "test": 2}
    assert manifest["seed"] == 764 and manifest["input"]["groups"] == 10 and manifest["pinned_groups"] == []
    assert assign_splits(records(), RATIOS, 765)["assignments"] != manifest["assignments"]
    assigned = apply_manifest(records(), manifest)
    for group in manifest["assignments"]:
        assert len({record["split"] for record in assigned if record["group_id"] == group}) == 1
    for family in {record["family_id"] for record in assigned if record["family_id"]}:
        assert len({record["split"] for record in assigned if record["family_id"] == family}) == 1


def test_pinned_and_contract_fixed_splits_are_honoured():
    items = records()
    manifest = assign_splits(items, RATIOS, 764)
    train_group = by_split(manifest, "train")[0]
    pinned = deepcopy(items)
    member(pinned, train_group, "random_benign")["split"] = "test"
    repinned = assign_splits(pinned, RATIOS, 764)
    assert repinned["assignments"][train_group] == "test" and repinned["pinned_groups"] == [train_group]
    held_out = deepcopy(items)
    member(held_out, train_group, "shared_malicious")["condition_source"] = "test_only"
    assert assign_splits(held_out, RATIOS, 764)["assignments"][train_group] == "test"
    conflicting = deepcopy(pinned)
    member(conflicting, train_group, "keyword_benign")["split"] = "train"
    with pytest.raises(ValueError, match="conflicting"):
        assign_splits(conflicting, RATIOS, 764)
    with pytest.raises(ValueError, match="contradicts a fixed split"):
        apply_manifest(held_out, manifest)


@pytest.mark.parametrize("ratios", [
    {"train": 0.7, "validation": 0.2, "test": 0.2}, {"train": 0.8, "test": 0.2},
    {"train": 1.0, "validation": 0.0, "test": 0.0}, {"train": "0.6", "validation": 0.2, "test": 0.2},
])
def test_invalid_ratios_are_refused(ratios):
    with pytest.raises(ValueError):
        assign_splits(records(), ratios, 764)


@pytest.mark.parametrize("seed", [-1, True, "764", 7.64])
def test_invalid_seeds_are_refused(seed):
    with pytest.raises(ValueError, match="seed"):
        assign_splits(records(), RATIOS, seed)


def test_fixture_passes_the_leakage_check():
    manifest = assign_splits(records(), RATIOS, 764)
    report = check_leakage(records(), manifest, near_duplicate_threshold=THRESHOLD)
    assert report["leakage_free"] and not any(report["error_counts"].values())
    assert report["benign_context_sentence_overlap"]["count"] == 0
    assert report["counts"]["test"]["families"] == 2


def test_a_deliberately_leaked_family_fails():
    items = records()
    manifest = assign_splits(items, RATIOS, 764)
    test_group, train_group = by_split(manifest, "test")[0], by_split(manifest, "train")[0]
    leaked = deepcopy(items)
    member(leaked, test_group, "semantic_benign")["group_id"] = train_group
    with pytest.raises(ValueError, match="Families span more than one group"):
        assign_splits(leaked, RATIOS, 764)
    with pytest.raises(ValueError, match="Families span"):
        validate_dataset(leaked)
    with pytest.raises(ContractError, match="families_across_splits") as failure:
        check_leakage(leaked, manifest, near_duplicate_threshold=THRESHOLD)
    report = failure.value.report
    assert report["leakage_free"] is False
    assert report["error_counts"]["families_across_splits"] == 1
    assert report["error_counts"]["test_families_seen_in_training"] == 1


def test_target_wording_crossing_splits_fails_even_as_benign_context():
    items = records()
    manifest = assign_splits(items, RATIOS, 764)
    test_group, train_group = by_split(manifest, "test")[0], by_split(manifest, "train")[0]
    target = member(items, train_group, "shared_malicious")["sentences"][1]["text"]
    copied = deepcopy(items)
    member(copied, test_group, "random_benign")["sentences"][0]["text"] = target
    with pytest.raises(ContractError) as exact:
        check_leakage(copied, assign_splits(copied, RATIOS, 764), near_duplicate_threshold=THRESHOLD)
    assert exact.value.report["error_counts"]["exact_target_sentences_across_splits"] == 1
    near = deepcopy(items)
    member(near, test_group, "random_benign")["sentences"][0]["text"] = target.rsplit(" ", 1)[0] + " Bob."
    with pytest.raises(ContractError) as similar:
        check_leakage(near, assign_splits(near, RATIOS, 764), near_duplicate_threshold=THRESHOLD)
    counts = similar.value.report["error_counts"]
    assert counts["exact_target_sentences_across_splits"] == 0
    # Both training targets carrying that wording (malicious member and benign counterpart) match.
    assert counts["near_target_sentences_across_splits"] == 2


def test_benign_context_overlap_is_reported_but_not_refused():
    items = records()
    manifest = assign_splits(items, RATIOS, 764)
    test_group, train_group = by_split(manifest, "test")[0], by_split(manifest, "train")[0]
    context = member(items, train_group, "random_benign")["sentences"][2]["text"]
    shared = deepcopy(items)
    member(shared, test_group, "random_benign")["sentences"][2]["text"] = context
    report = check_leakage(shared, assign_splits(shared, RATIOS, 764), near_duplicate_threshold=THRESHOLD)
    assert report["leakage_free"] and report["benign_context_sentence_overlap"]["count"] == 1


def test_duplicate_records_across_splits_fail():
    items = records()
    manifest = assign_splits(items, RATIOS, 764)
    test_group, train_group = by_split(manifest, "test")[0], by_split(manifest, "train")[0]
    copied = deepcopy(items)
    source = member(items, train_group, "random_benign")
    target = member(copied, test_group, "random_benign")
    target["query"], target["sentences"] = source["query"], deepcopy(source["sentences"])
    with pytest.raises(ValueError, match="Exact duplicate records"):
        validate_dataset(copied)
    with pytest.raises(ContractError) as failure:
        check_leakage(copied, assign_splits(copied, RATIOS, 764), near_duplicate_threshold=THRESHOLD)
    assert failure.value.report["error_counts"]["exact_duplicate_records_across_splits"] == 1


def test_training_selection_never_includes_held_out_records():
    items = records()
    manifest = assign_splits(items, RATIOS, 764)
    train_groups = set(by_split(manifest, "train"))
    for condition in ("m1_random", "m2_keyword", "m3_semantic"):
        selected = training_records(items, manifest, condition)
        assert len(selected) == 12 and {record["split"] for record in selected} == {"train"}
        assert {record["group_id"] for record in selected} == train_groups
    assert training_records(items, manifest, "m0_base") == []
    test_group = by_split(manifest, "test")[0]
    held_out = deepcopy(items)
    member(held_out, test_group, "shared_malicious")["condition_source"] = "test_only"
    relabelled = deepcopy(assign_splits(held_out, RATIOS, 764))
    relabelled["assignments"][test_group] = "train"
    with pytest.raises(ValueError, match="contradicts a fixed split"):
        training_records(held_out, relabelled, "m3_semantic")
    changed = deepcopy(items)
    changed[0]["sentences"][0]["text"] = "Edited after the split was made."
    with pytest.raises(ValueError, match="changed since the split manifest"):
        training_records(changed, manifest, "m3_semantic")
