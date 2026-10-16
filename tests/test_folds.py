import json
import math
import random
from collections import Counter
from copy import deepcopy
from pathlib import Path

import pytest

from rag_cad.cli import main
from rag_cad.data.folds import (
    FOLD_FIELDS,
    assign_folds,
    check_round,
    family_table,
    round_manifest,
    validate_folds,
)
from rag_cad.data.jsonl import load_records, read_jsonl
from rag_cad.data.schema import ContractError
from rag_cad.evaluation.bow_baseline import NaiveBayes, features, format_table, run_baseline

ROOT = Path(__file__).resolve().parents[1]
AUGMENTATION = ROOT / "datasets/raw/augmentation"
FAMILIES = AUGMENTATION / "families"
MANIFEST = AUGMENTATION / "family_manifest.jsonl"
FOLDS = AUGMENTATION / "folds_v1.jsonl"


@pytest.fixture(scope="module")
def data():
    records, _ = load_records(FAMILIES)
    return records, read_jsonl(MANIFEST)


@pytest.fixture(scope="module")
def assigned(data):
    return assign_folds(*data, 764)


def test_assignment_is_deterministic_and_matches_the_tracked_artefact(data, assigned):
    records, manifest = data
    rows, summary = assigned
    shuffled_records, shuffled_manifest = list(records), list(manifest)
    random.Random(1).shuffle(shuffled_records)
    random.Random(2).shuffle(shuffled_manifest)
    assert assign_folds(shuffled_records, shuffled_manifest, 764) == (rows, summary)
    assert read_jsonl(FOLDS) == rows
    assert json.loads((AUGMENTATION / "folds_v1.summary.json").read_text(encoding="utf-8"))["by_role"] \
        == summary["by_role"]
    assert assign_folds(records, manifest, 765)[0] != rows
    assert summary["seed"] == 764


def test_every_family_once_and_no_family_or_group_split(data, assigned):
    records, _ = data
    rows, _ = assigned
    keyed = validate_folds(rows)
    assert len(rows) == len(keyed) == 200 and all(set(row) == set(FOLD_FIELDS) for row in rows)
    assert {record["family_id"] for record in records if record["family_id"]} == set(keyed)
    fold_of_group = {row["group_id"]: row["fold"] for row in rows}
    assert len(fold_of_group) == 200
    for round_number in range(1, 6):
        manifest = round_manifest(records, rows, round_number)
        held = [record for record in records if manifest["assignments"][record["group_id"]] == "test"]
        assert len(held) == 160 and Counter(record["group_id"] for record in held) == Counter(
            {group: 4 for group, fold in fold_of_group.items() if fold == round_number})


def test_role_balance_is_exact_and_category_cells_differ_by_at_most_one(assigned):
    rows, summary = assigned
    roles = Counter((row["fold"], row["semantic_role"]) for row in rows)
    assert set(roles.values()) == {5} and len(roles) == 40
    cells = Counter((row["fold"], row["semantic_role"], row["attack_category"]) for row in rows)
    for role in {row["semantic_role"] for row in rows}:
        for category in ("task_type", "operational"):
            values = [cells[(fold, role, category)] for fold in range(1, 6)]
            assert max(values) - min(values) <= 1
    totals = Counter((row["fold"], row["attack_category"]) for row in rows)
    assert max(totals[(fold, "task_type")] for fold in range(1, 6)) \
        - min(totals[(fold, "task_type")] for fold in range(1, 6)) <= 1
    assert summary["balance"]["by_role"]["max_spread_between_folds"] == 0
    assert summary["balance"]["by_role_category"]["max_spread_between_folds"] <= 1
    assert summary["families_per_fold"] == {str(fold): 40 for fold in range(1, 6)}


def test_family_table_refuses_inconsistent_inputs(data):
    records, manifest = data
    with pytest.raises(ValueError, match="different families"):
        family_table(records, manifest[1:])
    changed = deepcopy(manifest)
    changed[0]["group_id"] = "unit_other"
    with pytest.raises(ValueError, match="group differs"):
        family_table(records, changed)
    with pytest.raises(ValueError, match="seed"):
        assign_folds(records, manifest, -1)


def test_fold_table_validation_refuses_split_or_repeated_families(assigned):
    rows, _ = assigned
    repeated = rows + [rows[0]]
    with pytest.raises(ValueError, match="twice"):
        validate_folds(repeated)
    split = deepcopy(rows)
    split[1]["group_id"] = split[0]["group_id"]
    split[1]["fold"] = split[0]["fold"] % 5 + 1
    with pytest.raises(ValueError, match="Group split"):
        validate_folds(split)


def test_one_round_is_leakage_free_and_a_shared_query_is_caught(data, assigned):
    records, _ = data
    rows, _ = assigned
    report = check_round(records, rows, 1, near_duplicate_threshold=0.8)
    assert report["leakage_free"] and report["held_out_families"] == 40
    assert not any(report["error_counts"].values()) and not any(report["cut_overlap_counts"].values())
    held = {row["group_id"] for row in rows if row["fold"] == 1}
    leaky = deepcopy(records)
    train = next(record for record in leaky if record["group_id"] not in held
                 and record["condition_source"] == "random_benign")
    test = next(record for record in leaky if record["group_id"] in held
                and record["condition_source"] == "random_benign")
    train["query"] = test["query"]
    with pytest.raises(ContractError) as error:
        check_round(leaky, rows, 1, near_duplicate_threshold=0.8)
    assert error.value.report["cut_overlap_counts"]["shared_queries"] == 1


def test_naive_bayes_matches_hand_computed_log_odds():
    model = NaiveBayes([["a", "b"], ["c"]], [1, 0])
    # vocabulary {a, b, c}; twin total 2, malicious total 1; equal priors; "z" unseen is ignored.
    expected = 2 * (math.log(2 / 5) - math.log(1 / 4))
    assert model.margin(["a", "a", "z"]) == pytest.approx(expected)
    assert features({"query": "Hello, World!", "sentences": [
        {"text": "Target here", "is_target": True}, {"text": "red  fox", "is_target": False}]}) \
        == ["hello", "world", "hello_world", "red", "fox", "red_fox"]


def test_port_reproduces_the_audit_figures_on_the_audit_folds(data, assigned):
    records, _ = data
    rows, _ = assigned
    families = sorted(row["family_id"] for row in rows)
    random.Random(764).shuffle(families)
    audit_fold = {family: index % 5 + 1 for index, family in enumerate(families)}
    result = run_baseline(records, [{**row, "fold": audit_fold[row["family_id"]]} for row in rows])
    assert result["overall"]["accuracy"] == 0.815 and result["overall"]["paired_share"] == 0.905
    assert result["per_fold_accuracy"] == [0.8375, 0.825, 0.7875, 0.8375, 0.7875]


def test_cli_assigns_checks_one_round_and_runs_the_baseline(tmp_path, capsys):
    folds = tmp_path / "folds_v1.jsonl"
    arguments = ["data", "assign-folds", "--input", str(FAMILIES), "--manifest", str(MANIFEST),
                 "--output", str(folds)]
    assert main(arguments) == 0
    assert folds.read_text(encoding="utf-8") == FOLDS.read_text(encoding="utf-8")
    assert (tmp_path / "folds_v1.summary.json").exists()
    assert main(arguments) == 2
    capsys.readouterr()
    assert main(["data", "check-leakage", "--input", str(FAMILIES), "--folds", str(folds), "--round", "2",
                 "--output", str(tmp_path / "leak.json")]) == 0
    assert json.loads(capsys.readouterr().out)["leakage_free"] is True
    assert main(["data", "check-leakage", "--input", str(FAMILIES), "--folds", str(folds),
                 "--output", str(tmp_path / "leak_no_round.json")]) == 2
    output = tmp_path / "bow.json"
    assert main(["evaluation", "bow-baseline", "--input", str(FAMILIES), "--manifest", str(MANIFEST),
                 "--folds", str(folds), "--output", str(output)]) == 0
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert "overall" in captured.err and result["overall"]["families"] == 200
    assert len(result["per_fold_accuracy"]) == 5 and set(result["per_attack_category"]) == {
        "operational", "task_type"}
    assert format_table(result).splitlines()[-1].startswith("overall")
    tampered = tmp_path / "tampered.jsonl"
    rows = read_jsonl(folds)
    rows[0]["semantic_role"] = "warning" if rows[0]["semantic_role"] != "warning" else "quotation"
    tampered.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    assert main(["evaluation", "bow-baseline", "--input", str(FAMILIES), "--manifest", str(MANIFEST),
                 "--folds", str(tampered), "--output", str(tmp_path / "bow2.json")]) == 2
