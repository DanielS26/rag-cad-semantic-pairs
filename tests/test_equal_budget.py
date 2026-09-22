from copy import deepcopy
from pathlib import Path

import pytest

from rag_cad.data.conditions import PRIMARY, compare_budgets, select, summarise
from rag_cad.data.jsonl import read_jsonl
from rag_cad.data.schema import ContractError
from rag_cad.data.split import apply_manifest, assign_splits

FIXTURE = Path(__file__).resolve().parents[1] / "tests/fixtures/phase2_families.jsonl"
RATIOS = {"train": 0.6, "validation": 0.2, "test": 0.2}


def assigned(records=None):
    records = read_jsonl(FIXTURE) if records is None else records
    return apply_manifest(records, assign_splits(records, RATIOS, 764))


def train_record(records, source):
    return next(record for record in records if record["split"] == "train"
                and record["condition_source"] == source)


def test_primary_conditions_share_one_sentence_budget():
    records = assigned()
    report = compare_budgets(records, PRIMARY, length_tolerance=0.25)
    assert report["equal_budget"] and report["shared_pools_identical"] and report["augmentation_units"] == 6
    rows = {condition: report["summaries"][condition]["sentence_rows"] for condition in PRIMARY}
    assert len(set(rows.values())) == 1 and rows["m3_semantic"] == 36
    for condition in PRIMARY:
        summary = report["summaries"][condition]
        assert summary["records"] == 12 and summary["malicious_rows"] == 6 and summary["benign_rows"] == 30
        assert set(summary["by_source"]) == {"shared_malicious", condition.split("_")[1] + "_benign"}
    assert summarise(select(records, "m0_base"))["sentence_rows"] == 0
    assert report["unit_character_ratio"]["enforced"] and report["unit_character_ratio"]["worst"] <= 1.25


def test_a_sentence_count_mismatch_is_refused():
    records = assigned()
    train_record(records, "keyword_benign")["sentences"].pop()
    with pytest.raises(ContractError, match="condition_counts_differ") as failure:
        compare_budgets(records, PRIMARY, length_tolerance=None)
    report = failure.value.report
    assert set(report["errors"]) == {"condition_counts_differ", "unequal_unit_sentence_counts"}
    assert set(report["count_mismatches"]) == {"sentence_rows", "benign_rows"}
    assert report["equal_budget"] is False and report["unit_character_ratio"]["enforced"] is False


def test_a_missing_control_variant_is_refused():
    records = assigned()
    records.remove(train_record(records, "random_benign"))
    with pytest.raises(ContractError) as failure:
        compare_budgets(records, PRIMARY, length_tolerance=None)
    assert "incomplete_augmentation_units" in failure.value.report["errors"]
    assert failure.value.report["count_mismatches"]["records"]["m1_random"] == 11


def test_length_tolerance_and_argument_checks():
    records = assigned()
    with pytest.raises(ContractError, match="unit_length_ratio_exceeds_tolerance"):
        compare_budgets(records, PRIMARY, length_tolerance=0.0)
    with pytest.raises(ValueError, match="At least two"):
        compare_budgets(records, ("m3_semantic",))
    with pytest.raises(ValueError, match="Unknown condition"):
        compare_budgets(records, ("m3_semantic", "m4_pairwise"))
    with pytest.raises(ValueError, match="Length tolerance"):
        compare_budgets(records, PRIMARY, length_tolerance=-0.1)
    with pytest.raises(ValueError, match="assigned splits"):
        select(read_jsonl(FIXTURE), "m3_semantic")


def test_summary_reports_document_and_sentence_levels():
    summary = summarise(assigned())
    assert summary["records"] == 40 and summary["sentence_rows"] == 120
    assert summary["malicious_rows"] == 10 and summary["target_rows"] == 20
    assert summary["by_split"] == {"test": 8, "train": 24, "validation": 8}
    assert summary["mean_sentences_per_record"] == 3.0 and summary["groups"] == 10
    assert summary["by_semantic_role"]["unauthorised_directive"] == 10
    empty = summarise([])
    assert empty["records"] == 0 and empty["mean_sentences_per_record"] == 0.0
    changed = deepcopy(assigned())
    changed[0]["domain"] = "other_domain"
    assert summarise(changed)["by_domain"]["other_domain"] == 1
