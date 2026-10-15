import json
from pathlib import Path

from rag_cad.data.batch_pipeline import length_hints
from rag_cad.data.cue_index import build_device_index
from rag_cad.data.edits import apply_edits
from rag_cad.data.edits import main as edits_main
from rag_cad.data.finalise_docs import main as docs_main
from rag_cad.data.jsonl import read_jsonl

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "tests/fixtures/phase2_families.jsonl"
MANIFEST = ROOT / "tests/fixtures/phase2_family_manifest.jsonl"


def test_apply_edits_requires_each_anchor_exactly_once(tmp_path):
    text = "alpha beta gamma beta"
    new, problems = apply_edits(text, [{"old": "alpha", "new": "ALPHA", "note": "first"}])
    assert new == "ALPHA beta gamma beta" and problems == []
    _, problems = apply_edits(text, [{"old": "beta", "new": "B"}, {"old": "missing", "new": "x"}])
    assert len(problems) == 2 and "occurs 2 times" in problems[0] and "occurs 0 times" in problems[1]
    target = tmp_path / "builder.py"
    target.write_text("x = 'old value'\n", encoding="utf-8")
    edits = tmp_path / "edits.json"
    edits.write_text(json.dumps([{"old": "'old value'", "new": "'new value'", "note": "reader MF1"}]), encoding="utf-8")
    assert edits_main(["--file", str(target), "--edits", str(edits), "--check"]) == 0
    assert target.read_text(encoding="utf-8") == "x = 'old value'\n"
    assert edits_main(["--file", str(target), "--edits", str(edits)]) == 0
    assert target.read_text(encoding="utf-8") == "x = 'new value'\n"
    assert edits_main(["--file", str(target), "--edits", str(edits)]) == 1  # the anchor is gone now


def test_device_index_is_compact_and_lists_devices_per_role():
    records = read_jsonl(RECORDS)
    entries = read_jsonl(MANIFEST)
    next(e for e in entries if e["family_id"] == "warning_0003")["justification"] += " device: caution-pointer."
    manifest = {e["family_id"]: e for e in entries}
    text = build_device_index([("02", records)], manifest)
    assert "## Devices by role" in text and "### warning (1): caution-pointer 1" in text
    assert "- warning_0003 [02] sentence_before; caution-pointer" in text
    assert "## Query openings by domain" in text and "## Source ids already used" in text
    assert "cue:" not in text  # the compact index carries no cue text


def test_length_hints_name_the_member_and_the_direction():
    rows = [{"family": "pilot_0001", "malicious": 300, "twin": 400, "random": 390, "keyword": 500, "pair": 0.75, "spread": 1.28}]
    hints = length_hints(rows)
    assert any("malicious 300 vs twin 400" in h and "+61" in h for h in hints)
    assert any("keyword control 500" in h and "-20" in h for h in hints)
    assert any("spread" in h for h in hints)


def test_finalise_docs_writes_archive_progress_and_data_card(tmp_path):
    repo = tmp_path / "repo"
    (repo / "docs").mkdir(parents=True)
    (repo / "docs/PROGRESS.md").write_text("# Progress\n\n## 2026-10-01 - Start\n\n- first\n", encoding="utf-8")
    (repo / "docs/DATA_CARD.md").write_text("# Data card\n", encoding="utf-8")
    findings = tmp_path / "batch_13_14_review_opus.md"
    findings.write_text("# Batches 13 and 14 review\n\nbody\n", encoding="utf-8")
    answers = tmp_path / "semantic_answers_batch_13_opus.json"
    answers.write_text("{}", encoding="utf-8")
    facts = {"batch": 13, "pair_role": "first", "pair_other": 14, "date": "2026-10-15", "reader": "Claude Opus 5",
             "review_commit": "abc1234", "findings_file": str(findings), "reader_answers": [str(answers)],
             "archive_dir": "docs/archive/review_batch_13_14_2026-10-15", "verdicts": "accept 2, fix 3",
             "findings_summary": "two query carriers", "applied": ["MF1 pilot_0121 query"], "declined": [{"item": "SF2", "reason": "breaks R5"}],
             "checker_proposals": "none", "exit_codes": "self-check 0, prescreen 0, validate 0", "twin_longer": "5 of 10",
             "hard_negative": "pilot_0125", "weak_cue": "pilot_0121", "families": 130, "coverage": "roles 16 each", "sheet": "sheet.md",
             "watch": ["keep queries asking"], "next": "batch 14", "sources": "eight ASB rows and two BIPIA strings",
             "deviations": "rows 240 and 242", "devices": "a, b, c", "first_family": "pilot_0121", "last_family": "pilot_0130"}
    facts_path = tmp_path / "facts.json"
    facts_path.write_text(json.dumps(facts), encoding="utf-8")
    assert docs_main(["--facts", str(facts_path), "--repo", str(repo)]) == 0
    archived = repo / "docs/archive/review_batch_13_14_2026-10-15/batch_13_14_review_opus.md"
    text = archived.read_text(encoding="utf-8")
    assert text.startswith("# Batches 13 and 14 review by the independent reader (Claude Opus 5)")
    assert "Batch 13: applied: MF1 pilot_0121 query." in text and "Batch 14's outcome is added below." in text
    assert text.endswith("# Batches 13 and 14 review\n\nbody\n")
    assert (repo / "docs/archive/review_batch_13_14_2026-10-15/semantic_answers_batch_13_opus.json").exists()
    progress = (repo / "docs/PROGRESS.md").read_text(encoding="utf-8")
    assert "## 2026-10-15 - Batch 13 Reviewed And Repaired" in progress and "Declined with reasons: SF2 (breaks R5)" in progress
    card = (repo / "docs/DATA_CARD.md").read_text(encoding="utf-8")
    assert "## Batch 13" in card and "pilot_0121 to pilot_0130" in card
    # the second batch of the pair replaces the placeholder sentence
    facts.update({"batch": 14, "pair_role": "second", "pair_other": 13, "applied": ["MF4 pilot_0133 heading"], "declined": [],
                  "first_family": "pilot_0131", "last_family": "pilot_0140", "reader_answers": []})
    facts_path.write_text(json.dumps(facts), encoding="utf-8")
    assert docs_main(["--facts", str(facts_path), "--repo", str(repo)]) == 0
    text = archived.read_text(encoding="utf-8")
    assert "Batch 14's outcome is added below." not in text and "Batch 14: applied: MF4 pilot_0133 heading." in text
    assert "## Batch 14" in (repo / "docs/DATA_CARD.md").read_text(encoding="utf-8")
