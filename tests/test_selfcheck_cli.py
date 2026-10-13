"""The `data selfcheck` command runs tools/selfcheck.py and fails on each rule family it covers."""

import json
from copy import deepcopy
from pathlib import Path

from rag_cad.cli import main
from rag_cad.data.jsonl import read_jsonl, write_jsonl

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "tests/fixtures/phase2_families.jsonl"
MANIFEST = ROOT / "tests/fixtures/phase2_family_manifest.jsonl"


def member(items, family, source):
    return next(r for r in items if r["family_id"] == family and r["condition_source"] == source)


def control(items, group, source):
    return next(r for r in items if r["group_id"] == group and r["condition_source"] == source)


def violated_batch(tmp_path):
    """One deliberate violation per rule family: M1, M4, M5, M6, M9, M12, M18."""
    items = read_jsonl(RECORDS)
    entries = read_jsonl(MANIFEST)
    # M1: twin target differs from the malicious target
    twin = member(items, "quote_0001", "semantic_benign")
    next(s for s in twin["sentences"] if s["is_target"])["text"] += " immediately"
    # M4: random control far longer than the twin
    control(items, "unit_negation_0002", "random_benign")["sentences"][0]["text"] += (
        " and the notice continues with a long description of the programme" * 4)
    # M4 spread: both controls within 20% of the twin but far apart from each other (validator max/min rule)
    spread_twin = member(items, "history_0006", "semantic_benign")
    spread_random = control(items, "unit_history_0006", "random_benign")
    spread_keyword = control(items, "unit_history_0006", "keyword_benign")
    twin_chars = sum(len(s["text"]) for s in spread_twin["sentences"])
    def pad_to(record, target_chars):
        current = sum(len(s["text"]) for s in record["sentences"])
        record["sentences"][-1]["text"] += " and the office" * max(0, (target_chars - current) // 15)
    pad_to(spread_random, int(twin_chars * 1.18))
    for s in spread_keyword["sentences"]:
        s["text"] = s["text"][: max(1, int(len(s["text"]) * 0.84))].rstrip() + "."
    # M5: malicious member far longer than its twin
    member(items, "warning_0003", "shared_malicious")["sentences"][0]["text"] += (
        " with an extended account of the circumstances" * 5)
    # M6: a token present in most twin contexts and no malicious member
    for family in ("analysis_0004", "translation_0005", "history_0006", "task_0007", "authorisation_0008",
                   "policy_0009", "heading_0010"):
        member(items, family, "semantic_benign")["sentences"][0]["text"] += " Zorblax noted it."
    # M9 mirror: every twin query opens with the same word while malicious queries vary
    for family in ("quote_0001", "negation_0002", "warning_0003", "analysis_0004", "translation_0005", "history_0006",
                   "task_0007", "authorisation_0008", "policy_0009", "heading_0010"):
        member(items, family, "semantic_benign")["query"] = f"Outline the {family} record for the file."
    # M9: the same query reused on two malicious members
    shared = member(items, "quote_0001", "shared_malicious")["query"]
    member(items, "negation_0002", "shared_malicious")["query"] = shared
    # M12: task_alignment with a non-query cue position
    next(e for e in entries if e["family_id"] == "task_0007")["cue_position"] = "policy"
    # M18: the weak_cue marker on a non-authorisation role, and on two families of one batch
    for family in ("quote_0001", "authorisation_0008"):
        next(e for e in entries if e["family_id"] == family)["justification"] += " weak_cue: attacker_writable."
    batch = tmp_path / "batch.jsonl"
    manifest = tmp_path / "manifest.jsonl"
    write_jsonl(batch, items)
    write_jsonl(manifest, entries)
    return batch, manifest


def test_selfcheck_command_fails_each_violated_rule_and_writes_the_report(tmp_path):
    batch, manifest = violated_batch(tmp_path)
    report_path = tmp_path / "report.json"
    code = main(["--repo", str(ROOT), "data", "selfcheck", "--batch", str(batch), "--manifest", str(manifest),
                 "--report", str(report_path)])
    assert code == 2
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["overall"] == "FAIL"
    assert report["binding"].startswith("tokenisation: rag_cad")
    assert any("max_over_min" in d for d in report["mechanical"]["M4_control_match"]["details"])
    m9 = json.dumps(report["mechanical"]["M9_queries"]["details"])
    assert "differs across pair sides" in m9 and "dominant twin query opener" in m9
    checks = report["mechanical"]
    for name in ("M1_target_identical", "M4_control_match", "M5_pair_length", "M6_lexical_skew",
                 "M9_queries", "M12_manifest_provenance", "M18_weak_cue_marker"):
        assert checks[name]["status"] == "FAIL", name
    assert "zorblax" in json.dumps(report["skew_table"]).lower()


def test_selfcheck_accepts_every_adapted_source_and_rejects_a_mismatched_id_prefix(tmp_path):
    """M12: a malicious target may come from any registered adapted source (BIPIA or ASB) with its own id prefix.

    The fixture families are hand-written, so every other family's malicious record fails this rule by
    design; the assertions look only at the family whose provenance is rewritten here.
    """
    def malicious_problems(report_path):
        details = json.loads(report_path.read_text(encoding="utf-8"))["mechanical"]["M12_manifest_provenance"]["details"]
        return [d["problem"] for d in details if d.get("family_id") == "quote_0001" and d.get("record") == "shared_malicious"]

    manifest = tmp_path / "manifest.jsonl"
    write_jsonl(manifest, read_jsonl(MANIFEST))
    cases = (("bipia_adapted", "bipia:text_attack_train:instruction:0", True),
             ("asb_adapted", "asb:all_attack_tools:17", True),
             ("asb_adapted", "bipia:text_attack_train:instruction:3", False))
    for index, (source, source_id, accepted) in enumerate(cases):
        items = read_jsonl(RECORDS)
        malicious = member(items, "quote_0001", "shared_malicious")
        malicious["provenance"].update(source_dataset=source, source_record_id=source_id, licence="MIT")
        batch, report_path = tmp_path / f"batch_{index}.jsonl", tmp_path / f"report_{index}.json"
        write_jsonl(batch, items)
        main(["--repo", str(ROOT), "data", "selfcheck", "--batch", str(batch), "--manifest", str(manifest),
              "--report", str(report_path)])
        problems = [p for p in malicious_problems(report_path) if "adapted source" in p]
        if accepted:
            assert problems == [], (source, source_id, problems)
        else:
            assert problems and "asb_adapted (asb:...)" in problems[0]

def test_selfcheck_semantic_gate_requires_answers_and_yes_rules(tmp_path):
    items = read_jsonl(RECORDS)
    batch, manifest = tmp_path / "batch.jsonl", tmp_path / "manifest.jsonl"
    write_jsonl(batch, items)
    write_jsonl(manifest, read_jsonl(MANIFEST))
    families = sorted({r["family_id"] for r in items if r["family_id"]})
    answers = {fam: {f"S{i}": "YES - fixture" for i in range(1, 13)} for fam in families}
    for fam in families:
        answers[fam]["S3"] = "NO"
        answers[fam]["S4"] = "NO"
    answers[families[0]]["S1"] = "NO - a second cue remains"
    answers[families[1]]["S4"] = "YES - becomes an injection"  # cue_position is sentence_before: must fail
    semantic = tmp_path / "semantic.json"
    semantic.write_text(json.dumps(answers), encoding="utf-8")
    report_path = tmp_path / "report.json"
    code = main(["--repo", str(ROOT), "data", "selfcheck", "--batch", str(batch), "--manifest", str(manifest),
                 "--semantic", str(semantic), "--report", str(report_path)])
    assert code == 2
    details = json.loads(report_path.read_text(encoding="utf-8"))["mechanical"]["S_semantic_answers"]["details"]
    problems = json.dumps(details)
    assert families[0] in problems and "S1" in problems
    assert "cue_position is not query" in problems
    # S3 YES without the manifest marker fails; the marker without S3 YES fails too
    answers["authorisation_0008"]["S3"] = "YES - HR could have written the cue"
    entries = read_jsonl(MANIFEST)
    next(e for e in entries if e["family_id"] == "policy_0009")["justification"] += " weak_cue: attacker_writable."
    manifest.unlink()
    write_jsonl(manifest, entries)
    semantic.write_text(json.dumps(answers), encoding="utf-8")
    report_path.unlink()
    assert main(["--repo", str(ROOT), "data", "selfcheck", "--batch", str(batch), "--manifest", str(manifest),
                 "--semantic", str(semantic), "--report", str(report_path)]) == 2
    problems = json.dumps(json.loads(report_path.read_text(encoding="utf-8"))["mechanical"]["S_semantic_answers"]["details"])
    assert "authorisation_0008" in problems and "lacks" in problems
    assert "policy_0009" in problems and "S3 is not YES" in problems
    # M19: a batch whose malicious members all share one attack_goal and drop the 'your response' phrasing
    # that every earlier target carried is flagged as a batch confound (WARN, not FAIL)
    items2 = read_jsonl(RECORDS)
    for r in items2:
        if r["condition_source"] == "shared_malicious":
            r["attack_goal"] = "task_hijack"
    batch2 = tmp_path / "batch2.jsonl"
    write_jsonl(batch2, items2)
    report3 = tmp_path / "r3.json"
    main(["--repo", str(ROOT), "data", "selfcheck", "--batch", str(batch2), "--manifest", str(manifest),
          "--previous", str(batch), "--report", str(report3)])
    m19 = json.loads(report3.read_text(encoding="utf-8"))["mechanical"]["M19_batch_confound"]
    assert m19["status"] == "WARN" and "same attack_goal" in json.dumps(m19["details"])
    # a Drive path is refused before the tool runs
    assert main(["--repo", str(ROOT), "data", "selfcheck", "--batch", "/content/drive/MyDrive/b.jsonl",
                 "--manifest", str(manifest), "--report", str(tmp_path / "r2.json")]) == 2
    assert not (tmp_path / "r2.json").exists()
    assert deepcopy(answers)  # keep the import honest
