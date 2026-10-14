import json
from pathlib import Path

from rag_cad.data.cue_index import build_cue_index, main
from rag_cad.data.jsonl import read_jsonl

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "tests/fixtures/phase2_families.jsonl"
MANIFEST = ROOT / "tests/fixtures/phase2_family_manifest.jsonl"


def test_cue_index_lists_every_twin_with_its_cue_device_and_the_used_sources(tmp_path):
    records = read_jsonl(RECORDS)
    entries = read_jsonl(MANIFEST)
    entry = next(e for e in entries if e["family_id"] == "warning_0003")
    entry["justification"] += " device: caution-pointer."
    manifest = {e["family_id"]: e for e in entries}
    text = build_cue_index([("02", records)], manifest)
    assert "### warning (1)" in text
    line = next(line for line in text.splitlines() if line.startswith("- warning_0003 "))
    assert "[02] sentence_before; device: caution-pointer;" in line and "cue: " in line
    twin = next(r for r in records if r["family_id"] == "warning_0003" and r["condition_source"] == "semantic_benign")
    assert twin["query"] in line
    assert "- quote_0001 [02] sentence_before; device: -;" in text
    assert "## Source ids already used" in text
    # query cue: the cue text is the query itself
    query_line = next(line for line in text.splitlines() if line.startswith("- analysis_0004 "))
    assert "query; device:" in query_line
    # the command-line entry point writes the same index from a directory of batch files
    families_dir = tmp_path / "families"
    families_dir.mkdir()
    (families_dir / "pilot_batch_02.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")
    manifest_path = tmp_path / "manifest.jsonl"
    manifest_path.write_text("".join(json.dumps(e) + "\n" for e in entries), encoding="utf-8")
    out = tmp_path / "review" / "cue_index.md"
    assert main(["--families-dir", str(families_dir), "--manifest", str(manifest_path), "--output", str(out)]) == 0
    assert out.read_text(encoding="utf-8") == text
