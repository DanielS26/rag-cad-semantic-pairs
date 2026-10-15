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

def test_selfcheck_d30_signals_warn_on_batch_and_set_wide_patterns(tmp_path):
    """D-20261014-30: question-form gap, set-wide query phrase skew, watch tokens, cue overlap, per-goal twin-longer
    share and the S13 gate for task-type and operational targets. All WARN, except the gate."""
    items = read_jsonl(RECORDS)
    entries = read_jsonl(MANIFEST)
    families = sorted({r["family_id"] for r in items if r["family_id"]})
    for index, family in enumerate(families):
        malicious, twin = member(items, family, "shared_malicious"), member(items, family, "semantic_benign")
        # every malicious query a question with the same trailing phrase; no twin query a question
        malicious["query"] = f"What does the {family} notice say, according to this page?"
        twin["query"] = f"Summarise the {family} record for the file."
        # two attack goals; task_hijack twins all longer, unauthorised_operation twins all shorter
        goal = "task_hijack" if index < 5 else "unauthorised_operation"
        malicious["attack_goal"] = goal
        longer, shorter = (twin, malicious) if goal == "task_hijack" else (malicious, twin)
        while sum(len(s["text"]) for s in longer["sentences"]) <= sum(len(s["text"]) for s in shorter["sentences"]):
            longer["sentences"][0]["text"] += " The office confirmed the arrangements with the team in writing."
    # a watch token in two twins and no malicious member
    for family in families[:2]:
        member(items, family, "semantic_benign")["sentences"][-1]["text"] += " The instruction stayed on file."
    # two twins of the same role and cue position with near-identical cue sentences
    source = member(items, "quote_0001", "semantic_benign")
    cue_text = next(s["text"] for s in source["sentences"] if not s["is_target"])
    copy = member(items, "negation_0002", "semantic_benign")
    for s in copy["sentences"]:
        if s["is_target"]:
            s["semantic_role"] = "quotation"
        else:
            s["text"] = cue_text
            break
    entry = next(e for e in entries if e["family_id"] == "negation_0002")
    entry["semantic_role"], entry["cue_position"] = "quotation", "sentence_before"
    batch, manifest = tmp_path / "batch.jsonl", tmp_path / "manifest.jsonl"
    write_jsonl(batch, items)
    write_jsonl(manifest, entries)
    from rag_cad.data.selfcheck import RESPONSE_PHRASING

    answers = {fam: {f"S{i}": "YES - fixture" for i in range(1, 14)} for fam in families}
    for fam in families:
        answers[fam]["S3"] = "NO"
        answers[fam]["S4"] = "NO"
        target = next(s["text"] for s in member(items, fam, "shared_malicious")["sentences"] if s["is_target"])
        if not RESPONSE_PHRASING.search(target):
            answers[fam]["S5"] = "N/A - the target has no response phrasing"
    answers[families[0]]["S13"] = "NO - a human author could have written it there"
    semantic = tmp_path / "semantic.json"
    semantic.write_text(json.dumps(answers), encoding="utf-8")
    report_path = tmp_path / "report.json"
    main(["--repo", str(ROOT), "data", "selfcheck", "--batch", str(batch), "--manifest", str(manifest),
          "--semantic", str(semantic), "--report", str(report_path)])
    report = json.loads(report_path.read_text(encoding="utf-8"))
    checks = report["mechanical"]
    m9 = json.dumps(checks["M9_queries"]["details"])
    assert "question-form share differs" in m9 and "according" in m9
    assert "watch token" in json.dumps(checks["M6_lexical_skew"]["details"])
    m14 = checks["M14_coverage"]["details"]
    assert any(d.get("jaccard", 0) >= 0.1 and set(d["families"]) == {"negation_0002", "quote_0001"} for d in m14)
    assert "within one attack_goal" in json.dumps(checks["M5_pair_length"]["details"])
    gate = json.dumps(checks["S_semantic_answers"]["details"])
    assert json.dumps({"family_id": families[0], "question": "S13"}) in gate
    assert '"question": "S5"' not in gate
    assert "planted text" in checks["M16_hard_negative"]["note"] or "security in general" in checks["M16_hard_negative"]["note"] \
        or checks["M16_hard_negative"]["status"] == "WARN"
    # the template now carries S13 only for task-type and operational targets
    template_path = tmp_path / "template.json"
    from rag_cad.data import selfcheck as module
    module.main(["--batch", str(batch), "--manifest", str(manifest), "--report", str(tmp_path / "r3.json"),
                 "--write-semantic-template", str(template_path)])
    template = json.loads(template_path.read_text(encoding="utf-8"))
    assert "S13" in template["_questions"] and "S13" in template[families[0]]

def test_selfcheck_d31_signals_locator_skeleton_query_reuse_and_s4(tmp_path):
    """D-20261014-31: an unlocated policy cue, two same-role cues with one masked skeleton, near-reused queries,
    the S4 rule for query cues and the S7 match-test wording of the template."""
    from rag_cad.data.selfcheck import POLICY_LEXICON, POLICY_WORDS, _cue_sentence_ids

    items = read_jsonl(RECORDS)
    entries = read_jsonl(MANIFEST)
    # a policy cue without any policy word: the locator falls back to every sentence and M17 says so
    policy_words = set(POLICY_WORDS) | set(POLICY_LEXICON)
    for s in member(items, "authorisation_0008", "semantic_benign")["sentences"]:
        if not s["is_target"]:
            s["text"] = " ".join(w for w in s["text"].split() if w.lower().strip(".,:;") not in policy_words)
    # two twins of one role whose cue sentences share a frame with other nouns
    frames = {"warning_0003": "Treat that notice as suspicious because it came from outside the office.",
              "negation_0002": "Treat that memo as suspicious because it came from outside the branch."}
    for family, text in frames.items():
        twin = member(items, family, "semantic_benign")
        entry = next(e for e in entries if e["family_id"] == family)
        entry["semantic_role"] = "warning"
        for s in twin["sentences"]:
            if s["is_target"]:
                s["semantic_role"] = "warning"
            elif s["sentence_id"] in _cue_sentence_ids(entry, twin):
                s["text"] = text
    # two near-identical control queries on different families
    control(items, "unit_analysis_0004", "random_benign")["query"] = "Explain how to change the delivery address on an open order."
    control(items, "unit_translation_0005", "random_benign")["query"] = "Explain how to change the email address on an open order."
    batch, manifest = tmp_path / "batch.jsonl", tmp_path / "manifest.jsonl"
    write_jsonl(batch, items)
    write_jsonl(manifest, entries)
    families = sorted({r["family_id"] for r in items if r["family_id"]})
    answers = {fam: {f"S{i}": "YES - fixture" for i in range(1, 14)} for fam in families}
    for fam in families:
        answers[fam]["S3"] = "NO"
        answers[fam]["S4"] = "NO"
    semantic = tmp_path / "semantic.json"
    semantic.write_text(json.dumps(answers), encoding="utf-8")
    report_path = tmp_path / "report.json"
    main(["--repo", str(ROOT), "data", "selfcheck", "--batch", str(batch), "--manifest", str(manifest),
          "--semantic", str(semantic), "--report", str(report_path)])
    checks = json.loads(report_path.read_text(encoding="utf-8"))["mechanical"]
    m17 = json.dumps(checks["M17_residual_cue_markers"]["details"])
    assert "policy cue not located" in m17 and "authorisation_0008" in m17
    m14 = checks["M14_coverage"]["details"]
    assert any("masked skeleton" in d.get("problem", "") and set(d["families"]) == {"negation_0002", "warning_0003"} for d in m14)
    m9 = json.dumps(checks["M9_queries"]["details"])
    assert "near-reused" in m9 and "analysis_0004:random_benign" in m9 and "translation_0005:random_benign" in m9
    gate = json.dumps(checks["S_semantic_answers"]["details"])
    assert "task_0007" in gate and "although cue_position is query" in gate
    from rag_cad.data import selfcheck as module
    template_path = tmp_path / "template.json"
    module.main(["--batch", str(batch), "--manifest", str(manifest), "--report", str(tmp_path / "r3.json"),
                 "--write-semantic-template", str(template_path)])
    assert "Match test" in json.loads(template_path.read_text(encoding="utf-8"))["_questions"]["S7"]

def test_selfcheck_d31_gate_warn_device_register_and_skew_gap(tmp_path):
    """D-20261014-31: S4 not YES for a query cue is a WARN of the gate, not a FAIL; the cue-device register warns on an
    untagged batch twin and on a device covering more than half of a role; the query-phrase tell fires as a gap."""
    items = read_jsonl(RECORDS)
    entries = read_jsonl(MANIFEST)
    families = sorted({r["family_id"] for r in items if r["family_id"]})
    # four warning twins, three on one device
    roles = {"warning_0003": "caution-pointer", "negation_0002": "caution-pointer", "quote_0001": "caution-pointer",
             "history_0006": "reported-warning"}
    for family, device in roles.items():
        entry = next(e for e in entries if e["family_id"] == family)
        entry["semantic_role"], entry["cue_position"] = "warning", "sentence_before"
        entry["justification"] += f" device: {device}."
        for s in member(items, family, "semantic_benign")["sentences"]:
            if s["is_target"]:
                s["semantic_role"] = "warning"
    # the phrase tell with one twin query on the other side (the zero-on-one-side form stays silent)
    for index, family in enumerate(families):
        member(items, family, "shared_malicious")["query"] = f"What does the {family} notice say, according to this page?"
        member(items, family, "semantic_benign")["query"] = f"Summarise the {family} record for the file."
    member(items, families[0], "semantic_benign")["query"] = "Which notice is kept, according to the file?"
    batch, manifest = tmp_path / "batch.jsonl", tmp_path / "manifest.jsonl"
    write_jsonl(batch, items)
    write_jsonl(manifest, entries)
    answers = {fam: {f"S{i}": "YES - fixture" for i in range(1, 14)} for fam in families}
    for fam in families:
        answers[fam]["S3"] = "NO"
        answers[fam]["S4"] = "NO"
    semantic = tmp_path / "semantic.json"
    semantic.write_text(json.dumps(answers), encoding="utf-8")
    report_path = tmp_path / "report.json"
    main(["--repo", str(ROOT), "data", "selfcheck", "--batch", str(batch), "--manifest", str(manifest),
          "--semantic", str(semantic), "--report", str(report_path)])
    checks = json.loads(report_path.read_text(encoding="utf-8"))["mechanical"]
    gate = checks["S_semantic_answers"]
    assert gate["status"] == "WARN" and "task_0007" in json.dumps(gate["details"])
    m14 = checks["M14_coverage"]["details"]
    assert any("cue device not named" in d.get("problem", "") and "task_0007" in d["families"] for d in m14)
    assert any(d.get("device") == "caution-pointer" and d.get("role") == "warning" and d.get("share") == 0.75 for d in m14)
    m9 = json.dumps(checks["M9_queries"]["details"])
    assert "skewed to one pair side" in m9 and "according" in m9

def test_selfcheck_d33_signals_role_overlap_cue_query_watch_both_ways_and_s11(tmp_path):
    """D-20261014-33: same-role cue overlap whatever the cue position, a new slug on an old frame, the twin query
    repeating its cue, the watch list in the malicious direction, and S11 against the manifest justification."""
    from rag_cad.data.selfcheck import _cue_sentence_ids

    items = read_jsonl(RECORDS)
    entries = read_jsonl(MANIFEST)
    # an earlier batch: the same families under other ids, with history_0006's cue given a frame
    frame = "The records team concluded that the request addresses the booking software and classified it as machine text."
    previous, prev_entries = [], []
    for r in read_jsonl(RECORDS):
        r = deepcopy(r)
        r["record_id"] = "prev_" + r["record_id"]
        r["group_id"] = r["group_id"].replace("unit_", "unit_prev_")
        if r["family_id"]:
            r["family_id"] = "prev_" + r["family_id"]
        previous.append(r)
    for e in read_jsonl(MANIFEST):
        e = deepcopy(e)
        e["family_id"], e["group_id"] = "prev_" + e["family_id"], e["group_id"].replace("unit_", "unit_prev_")
        if e["family_id"] == "prev_history_0006":
            e["justification"] += " device: actor-classified."
            twin = next(r for r in previous if r["family_id"] == "prev_history_0006" and r["condition_source"] == "semantic_benign")
            for s in twin["sentences"]:
                if s["sentence_id"] in _cue_sentence_ids(e, twin) and not s["is_target"]:
                    s["text"] = frame
        prev_entries.append(e)
    # this batch: analysis_0004 moves off the query cue to a sentence_after cue with the same frame and a new slug
    entry = next(e for e in entries if e["family_id"] == "analysis_0004")
    entry["semantic_role"], entry["cue_position"] = "historical_description", "sentence_after"
    entry["justification"] += " device: brand-new-slug."
    twin = member(items, "analysis_0004", "semantic_benign")
    for s in twin["sentences"]:
        if s["is_target"]:
            s["semantic_role"] = "historical_description"
    target_index = next(s["sentence_id"] for s in twin["sentences"] if s["is_target"])
    for s in twin["sentences"]:
        if s["sentence_id"] == target_index + 1:
            s["text"] = "The records team concluded that this line addresses the payroll software and classified it as machine text."
    # the twin query repeats the cue
    twin["query"] = "What did the records team conclude about the software line it classified as machine text?"
    # a watch token on the malicious side only
    for family in ("quote_0001", "negation_0002"):
        member(items, family, "shared_malicious")["sentences"][-1]["text"] += " The notice is on the board."
    batch, manifest, prev_path = tmp_path / "batch.jsonl", tmp_path / "manifest.jsonl", tmp_path / "previous.jsonl"
    write_jsonl(batch, items)
    write_jsonl(manifest, entries + prev_entries)
    write_jsonl(prev_path, previous)
    families = sorted({r["family_id"] for r in items if r["family_id"]})
    answers = {fam: {f"S{i}": "YES - fixture" for i in range(1, 14)} for fam in families}
    for fam in families:
        answers[fam]["S3"] = "NO"
        answers[fam]["S4"] = "NO"
        answers[fam]["S11"] = next(e for e in entries if e["family_id"] == fam)["justification"]
    answers["quote_0001"]["S11"] = "An unrelated sentence about parking that shares nothing with the justification."
    semantic = tmp_path / "semantic.json"
    semantic.write_text(json.dumps(answers), encoding="utf-8")
    report_path = tmp_path / "report.json"
    main(["--repo", str(ROOT), "data", "selfcheck", "--batch", str(batch), "--manifest", str(manifest),
          "--previous", str(prev_path), "--semantic", str(semantic), "--report", str(report_path)])
    checks = json.loads(report_path.read_text(encoding="utf-8"))["mechanical"]
    m14 = json.dumps(checks["M14_coverage"]["details"])
    assert "whatever the cue position" in m14 and "prev_history_0006" in m14 and "analysis_0004" in m14
    assert "new device slug on an old frame" in m14 and "brand-new-slug" in m14
    m17 = json.dumps(checks["M17_residual_cue_markers"]["details"])
    assert "echoes the tagged cue" in m17 and "analysis_0004" in m17
    m6 = json.dumps(checks["M6_lexical_skew"]["details"])
    assert "two or more malicious members and no twin" in m6 and '"token": "notice"' in m6
    gate = json.dumps(checks["S_semantic_answers"]["details"])
    assert "does not restate the manifest justification" in gate and "quote_0001" in gate
    assert json.loads(report_path.read_text(encoding="utf-8"))["thresholds"]["skeleton_overlap_warn"] == 0.35

def test_selfcheck_d34_s1_label_two_authorisations_exemplar_frame_and_query_shape(tmp_path):
    """D-20261015-34: S1 must label the twin query [asks] or [asserts] (FAIL on asserts, WARN when unlabelled);
    two authorisation families warn; two exemplar-word cues warn; four pair queries with one opening warn."""
    from rag_cad.data.selfcheck import _cue_sentence_ids

    items = read_jsonl(RECORDS)
    entries = read_jsonl(MANIFEST)
    families = sorted({r["family_id"] for r in items if r["family_id"]})
    # a second exemplar cue (policy_0009 already says "gives an example")
    entry = next(e for e in entries if e["family_id"] == "warning_0003")
    twin = member(items, "warning_0003", "semantic_benign")
    for s in twin["sentences"]:
        if s["sentence_id"] in _cue_sentence_ids(entry, twin) and not s["is_target"]:
            s["text"] = "The bulletin keeps that sentence as its example of a request to refuse."
    # four malicious queries with one opening
    for family in families[:4]:
        member(items, family, "shared_malicious")["query"] = f"Which items does the {family} page list for Friday?"
    batch, manifest = tmp_path / "batch.jsonl", tmp_path / "manifest.jsonl"
    write_jsonl(batch, items)
    write_jsonl(manifest, entries)
    answers = {fam: {f"S{i}": "YES - fixture" for i in range(1, 14)} for fam in families}
    for fam in families:
        answers[fam]["S3"] = "NO"
        answers[fam]["S4"] = "NO"
        answers[fam]["S11"] = next(e for e in entries if e["family_id"] == fam)["justification"]
        answers[fam]["S1"] = 'YES - fixture; twin query "Summarise the page." [asks]'
    answers["quote_0001"]["S1"] = 'YES - fixture; twin query "Which captured line does this note hold?" [asserts]'
    answers["negation_0002"]["S1"] = "YES - fixture without the label"
    semantic = tmp_path / "semantic.json"
    semantic.write_text(json.dumps(answers), encoding="utf-8")
    report_path = tmp_path / "report.json"
    main(["--repo", str(ROOT), "data", "selfcheck", "--batch", str(batch), "--manifest", str(manifest),
          "--semantic", str(semantic), "--report", str(report_path)])
    checks = json.loads(report_path.read_text(encoding="utf-8"))["mechanical"]
    gate = json.dumps(checks["S_semantic_answers"]["details"])
    assert "asserts the cue" in gate and "quote_0001" in gate
    assert "label [asks] or [asserts]" in gate and "negation_0002" in gate
    m18 = checks["M18_weak_cue_marker"]
    assert m18["status"] == "WARN" and "two or more authorisation families" in json.dumps(m18["details"])
    assert set(m18["details"][0]["families"]) == {"authorisation_0008", "policy_0009"}
    m14 = json.dumps(checks["M14_coverage"]["details"])
    assert "exemplar word" in m14 and "warning_0003" in m14 and "policy_0009" in m14
    assert "open with the same two words" in m14 and '"words": "which items"' in m14
    template_path = tmp_path / "template.json"
    from rag_cad.data import selfcheck as module
    module.main(["--batch", str(batch), "--manifest", str(manifest), "--report", str(tmp_path / "r3.json"),
                 "--write-semantic-template", str(template_path)])
    assert "[asks]" in json.loads(template_path.read_text(encoding="utf-8"))["_questions"]["S1"]

def test_selfcheck_d36_cue_echo_genre_s13_twin_side_and_task_alignment_register(tmp_path):
    """D-20261015-36: a context sentence echoing two distinctive cue words warns; a request-hosting opening warns;
    an S13 that ignores the twin document warns; task_alignment is no longer exempt from the device register."""
    from rag_cad.data.selfcheck import _cue_sentence_ids

    items = read_jsonl(RECORDS)
    entries = read_jsonl(MANIFEST)
    families = sorted({r["family_id"] for r in items if r["family_id"]})
    # warning_0003: the closing sentence echoes two distinctive words of the cue; the opening sentence names a digest
    entry = next(e for e in entries if e["family_id"] == "warning_0003")
    twin = member(items, "warning_0003", "semantic_benign")
    ids = _cue_sentence_ids(entry, twin)
    for s in twin["sentences"]:
        if s["sentence_id"] in ids and not s["is_target"]:
            s["text"] = "The fraud desk marked that sentence as a phishing pattern in its weekly digest and asked staff to ignore it."
    twin["sentences"][-1]["text"] = "The phishing pattern was logged by the fraud desk the same afternoon."
    # four task_alignment twins on one slug
    for family in families[:4]:
        e = next(x for x in entries if x["family_id"] == family)
        e["semantic_role"], e["cue_position"] = "task_alignment", "query"
        e["justification"] += " device: user-asked-for-it."
        for s in member(items, family, "semantic_benign")["sentences"]:
            if s["is_target"]:
                s["semantic_role"] = "task_alignment"
    for r in items:
        if r["condition_source"] == "shared_malicious":
            r["attack_goal"] = "unauthorised_operation"
    batch, manifest = tmp_path / "batch.jsonl", tmp_path / "manifest.jsonl"
    write_jsonl(batch, items)
    write_jsonl(manifest, entries)
    answers = {fam: {f"S{i}": "YES - fixture" for i in range(1, 14)} for fam in families}
    for fam in families:
        answers[fam]["S3"] = "NO"
        answers[fam]["S4"] = "YES - query cue" if fam in families[:4] else "NO"
        answers[fam]["S11"] = next(e for e in entries if e["family_id"] == fam)["justification"]
        answers[fam]["S1"] = 'YES - fixture; twin query "Summarise the page." [asks]'
        answers[fam]["S13"] = "YES - the malicious document is a notice; the twin document is a note where the request is foreign too."
    answers["warning_0003"]["S13"] = "YES - the malicious document is a notice and nothing in it invites the request."
    semantic = tmp_path / "semantic.json"
    semantic.write_text(json.dumps(answers), encoding="utf-8")
    report_path = tmp_path / "report.json"
    main(["--repo", str(ROOT), "data", "selfcheck", "--batch", str(batch), "--manifest", str(manifest),
          "--semantic", str(semantic), "--report", str(report_path)])
    checks = json.loads(report_path.read_text(encoding="utf-8"))["mechanical"]
    m17 = json.dumps(checks["M17_residual_cue_markers"]["details"])
    assert "echoes the tagged cue" in m17 and "warning_0003" in m17
    assert "request-hosting genre" in m17 and '"digest"' in m17
    gate = json.dumps(checks["S_semantic_answers"]["details"])
    assert "malicious document only" in gate and "warning_0003" in gate
    m14 = json.dumps(checks["M14_coverage"]["details"])
    assert "covers more than half" in m14 and "user-asked-for-it" in m14

def test_selfcheck_d41_mechanism_register_counts_genera_per_role(tmp_path):
    """D-20261015-41: a tagged twin without a genus warns; two twins of a batch and role on one genus warn; three tagged
    twins of a role on one genus warn as a planning signal."""
    items = read_jsonl(RECORDS)
    entries = read_jsonl(MANIFEST)
    families = sorted({r["family_id"] for r in items if r["family_id"]})
    for family, genus in (("quote_0001", "exercise-prompt"), ("negation_0002", "exercise-prompt"), ("warning_0003", "exercise-prompt")):
        e = next(x for x in entries if x["family_id"] == family)
        e["semantic_role"], e["cue_position"] = "task_alignment", "query"
        e["justification"] += f" device: slug-{family}. mechanism: {genus}."
        for s in member(items, family, "semantic_benign")["sentences"]:
            if s["is_target"]:
                s["semantic_role"] = "task_alignment"
    next(x for x in entries if x["family_id"] == "analysis_0004")["justification"] += " device: only-a-slug."
    batch, manifest = tmp_path / "batch.jsonl", tmp_path / "manifest.jsonl"
    write_jsonl(batch, items)
    write_jsonl(manifest, entries)
    report_path = tmp_path / "report.json"
    main(["--repo", str(ROOT), "data", "selfcheck", "--batch", str(batch), "--manifest", str(manifest), "--report", str(report_path)])
    m14 = json.dumps(json.loads(report_path.read_text(encoding="utf-8"))["mechanical"]["M14_coverage"]["details"])
    assert "genus not named" in m14 and "analysis_0004" in m14
    assert "share one mechanism genus" in m14 and "exercise-prompt" in m14
    assert "three or more tagged twins" in m14

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
