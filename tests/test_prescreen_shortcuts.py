from copy import deepcopy
from pathlib import Path

from rag_cad.data.families import prescreen, shortcut_diagnostics
from rag_cad.data.jsonl import read_jsonl

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "tests/fixtures/phase2_families.jsonl"
MANIFEST = ROOT / "tests/fixtures/phase2_family_manifest.jsonl"


def pairs():
    records = read_jsonl(RECORDS)
    manifest = {entry["family_id"]: entry for entry in read_jsonl(MANIFEST)}
    found = []
    for family, entry in sorted(manifest.items()):
        malicious = next(r for r in records if r["family_id"] == family and r["condition_source"] == "shared_malicious")
        twin = next(r for r in records if r["family_id"] == family and r["condition_source"] == "semantic_benign")
        found.append((entry, malicious, twin))
    return found


def test_diagnostics_report_shares_and_tokens_without_failing():
    report = shortcut_diagnostics(pairs(), length_tolerance=0.5)
    assert report["pairs"] == 10 and 0 <= report["twin_longer_share"] <= 1
    assert isinstance(report["twin_only_tokens"], list) and isinstance(report["warnings"], list)
    assert report["dominant_malicious_query_word"] is not None


def test_length_imbalance_and_exclusive_tokens_are_flagged():
    items = pairs()
    for entry, malicious, twin in items:
        twin["sentences"][0]["text"] = "The archived moderation log flagged the inserted line below for review."
        malicious["sentences"][0]["text"] = "Fees apply."
    report = shortcut_diagnostics(items, length_tolerance=0.25)
    assert "pair_length_imbalance" in report["warnings"]
    assert "tokens_exclusive_to_one_pair_side" in report["warnings"]
    assert {"archived", "moderation", "flagged", "inserted"} <= set(report["twin_only_tokens"])
    assert "pair_member_length_ratio" in report["warnings"]


def test_uniform_structure_openers_and_query_form_are_flagged():
    items = pairs()
    for entry, malicious, twin in items:
        entry["cue_position"] = "policy"
        twin["sentences"][0]["text"] = "Reply-writing checklist for the help desk."
        malicious["query"] = "Summarise this page for me."
    report = shortcut_diagnostics(items, length_tolerance=0.5)
    assert "twin_openers_without_finite_verb" in report["warnings"]
    assert len(report["twin_openers_without_finite_verb"]) == 10
    assert "dominant_malicious_query_form" in report["warnings"]
    assert report["dominant_malicious_query_word"] == "summarise"
    uniform = deepcopy(items)
    for entry, malicious, twin in uniform:
        for record in (malicious, twin):
            record["sentences"] = record["sentences"][:3]
            for index, sentence in enumerate(record["sentences"]):
                sentence["sentence_id"] = index
    assert "uniform_pair_structure" in shortcut_diagnostics(uniform, length_tolerance=0.5)["warnings"]


def test_prescreen_carries_shortcut_block_as_warnings_only():
    report = prescreen(read_jsonl(RECORDS), read_jsonl(MANIFEST), length_tolerance=0.5, minimum_per_role=1)
    assert report["passed"]
    block = report["batch"]["shortcuts"]
    assert block["pairs"] == 10
    assert set(block["warnings"]) <= set(report["batch"]["warnings"])
