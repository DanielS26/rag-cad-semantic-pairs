import io
import json
import tarfile
from pathlib import Path

import pytest
import yaml

from rag_cad.cli import main
from rag_cad.data.cad_release_adapter import (
    FALLBACK_GOAL,
    adapt_archive,
    adapt_release,
    member_suite,
    scorer_record,
)
from rag_cad.data.jsonl import read_jsonl
from rag_cad.data.schema import validate_record
from rag_cad.operations.provenance import CAD_COMMIT, sha256

TRAIN = "training_data_original"
TEST = "testing_data_original"
PARA = "training_data_paraphrased"


def raw(units: int, span: tuple[int, int], *, user_task="user_task_1", injection_task="injection_task_1",
        total_units=None, **extra) -> dict:
    record = {"user": "Synthetic user query.", "data": "inert", "injection": "inert", "injected": "inert",
              "sentence_segments": "\n".join(f"[{i}] Synthetic unit {i} with\ttab." if i == 0 else
                                             f"[{i}] Synthetic unit {i}." for i in range(units)),
              "injection_span_unit": {"start": span[0], "end": span[1]},
              "user_task_id": user_task, "injection_task_id": injection_task}
    if total_units is not None:
        record["total_units"] = total_units
    return record | extra


TRAIN_MEMBERS = {
    f"{TRAIN}/agentdojo_banking_scenarios/banking_scenario_0/user_task_1/injection_task_1.json": raw(6, (2, 3), total_units=6),
    f"{TRAIN}/agentdojo_banking_scenarios/banking_scenario_0/user_task_2/injection_task_1.json": raw(5, (4, 4)),
    f"{TRAIN}/agentdojo_slack_scenarios/slack_scenario_3/user_task_0/injection_task_2.json": raw(4, (0, 1), total_units=4, injection_task="injection_task_2"),
    f"{TRAIN}/agentdojo_travel_scenarios/travel_scenario_1/user_task_0/injection_task_0.json": raw(3, (1, 1), injection_task=None),
}
TEST_MEMBERS = {
    f"{TEST}/banking/user_task_0/injection_task_0.json": raw(5, (1, 3), total_units=5, suite_name="banking",
                                                             injection_span_char={"start": 0, "end": 1}),
    f"{TEST}/slack/user_task_0/injection_task_1.json": raw(4, (3, 3), total_units=4, suite_name="slack"),
    f"{TEST}/travel/user_task_1/injection_task_0.json": raw(3, (0, 0), total_units=3, suite_name="travel"),
}
PARA_MEMBERS = {
    f"{PARA}/agentdojo_banking_scenarios/banking_scenario_0/user_task_1/injection_task_1__authority_0.json":
        raw(6, (2, 3), total_units=9, style="authority",
            source_file="agentdojo_banking_scenarios/banking_scenario_0/user_task_1/injection_task_1.json"),
    f"{PARA}/agentdojo_banking_scenarios/banking_scenario_0/user_task_1/injection_task_1__authority_1.json":
        raw(6, (2, 3), style="authority",
            source_file="banking_scenario_0/user_task_1/injection_task_1.json"),
    f"{PARA}/agentdojo_slack_scenarios/slack_scenario_3/user_task_0/injection_task_2__urgency_0.json":
        raw(4, (0, 1), total_units=4, style="urgency",
            source_file="slack_scenario_3/user_task_9/injection_task_2.json"),
}


def archive(path: Path, members: dict, extra_files: dict | None = None) -> Path:
    with tarfile.open(path, "w:gz") as handle:
        for name, payload in {**members, **(extra_files or {})}.items():
            data = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            handle.addfile(info, io.BytesIO(data))
    return path


def counts(members: dict, *, paraphrased: bool = False) -> dict:
    rows = malicious = mismatches = 0
    for record in members.values():
        units = record["sentence_segments"].count("\n") + 1
        span = record["injection_span_unit"]
        rows += units
        malicious += span["end"] - span["start"] + 1
        if paraphrased and record.get("total_units") not in (None, units):
            mismatches += 1
    return {"records": len(members), "rows": rows, "malicious": malicious, "benign": rows - malicious,
            "count_mismatches": mismatches}


def release(tmp_path: Path, *, train=TRAIN_MEMBERS, test=TEST_MEMBERS, para=PARA_MEMBERS,
            train_counts=None) -> tuple[dict, Path]:
    source = tmp_path / "release"
    source.mkdir(parents=True)
    files = {}
    for name, members, kind, flag in ((f"{TRAIN}.tar.gz", train, "original_train", False),
                                      (f"{TEST}.tar.gz", test, "original_test", False),
                                      (f"{PARA}.tar.gz", para, "paraphrased_train", True)):
        extra = {f"{TEST}/banking/suite.yaml": b"inert: true\n"} if kind == "original_test" else None
        path = archive(source / name, members, extra)
        files[name] = {"repository_type": "dataset", "kind": kind, "bytes": path.stat().st_size,
                       "sha256": sha256(path), "counts": counts(members, paraphrased=flag)}
    if train_counts is not None:
        files[f"{TRAIN}.tar.gz"]["counts"] = train_counts
    checkpoint = source / "classifier_fullcad.pt"
    checkpoint.write_bytes(b"not a checkpoint")
    files["classifier_fullcad.pt"] = {"repository_type": "model", "kind": "checkpoint",
                                      "bytes": checkpoint.stat().st_size, "sha256": sha256(checkpoint)}
    spec = {"cad_commit": CAD_COMMIT, "data_repository": "tavialiu/CAD-data",
            "models_repository": "tavialiu/CAD-models", "data_revision": "f" * 40, "models_revision": "5" * 40,
            "data_licence": "CC-BY-4.0", "model_licence": "MIT", "files": files}
    return spec, source


def test_member_suite_follows_the_upstream_layouts():
    assert member_suite(f"{TRAIN}/agentdojo_banking_scenarios/banking_scenario_0/user_task_1/x.json") == "banking"
    assert member_suite(f"{TEST}/travel/user_task_0/injection_task_0.json") == "travel"
    assert member_suite("slack_scenario_3/user_task_0/injection_task_2.json") == "slack"
    assert member_suite(f"{TEST}/loose.json") == "unknown"


def test_scorer_record_fields_and_notes():
    name = f"{TRAIN}/agentdojo_banking_scenarios/banking_scenario_0/user_task_1/injection_task_1.json"
    record, note = scorer_record(name, TRAIN_MEMBERS[name], "original_train")
    assert record["record_id"] == "cad_original_train:agentdojo_banking_scenarios/banking_scenario_0/user_task_1/injection_task_1"
    assert record["group_id"] == "cad_scenario:banking_scenario_0" and record["domain"] == "banking"
    assert record["split"] is None and record["condition_source"] == "base" and record["family_id"] is None
    assert record["attack_goal"] == "banking_injection_task_1" and record["pair_member"] == "unpaired"
    assert [s["label"] for s in record["sentences"]] == [0, 0, 1, 1, 0, 0]
    assert [s["is_target"] for s in record["sentences"]] == [False, False, True, True, False, False]
    assert {s["semantic_role"] for s in record["sentences"] if s["label"]} == {"injected_instruction"}
    assert record["provenance"] == {"source_dataset": "cad_original_train", "source_record_id": name,
                                    "generator_model": None, "generator_prompt_hash": None,
                                    "licence": "CC-BY-4.0", "review_status": "unreviewed"}
    assert validate_record(record, require_split=False) == record
    assert note["injection_span_unit"] == [2, 3] and note["supplied_total_units"] == 6
    assert note["user_task_id"] == "user_task_1" and len(note["content_hash"]) == 64
    assert "Synthetic" not in json.dumps(note)


def test_test_archive_records_are_test_only_and_goal_falls_back_without_task_id():
    name = f"{TEST}/banking/user_task_0/injection_task_0.json"
    record, _ = scorer_record(name, TEST_MEMBERS[name], "original_test")
    assert record["condition_source"] == "test_only" and record["group_id"] == "cad_original_test:banking/user_task_0"
    assert record["provenance"]["source_dataset"] == "cad_original_test"
    travel = f"{TRAIN}/agentdojo_travel_scenarios/travel_scenario_1/user_task_0/injection_task_0.json"
    record, _ = scorer_record(travel, TRAIN_MEMBERS[travel], "original_train")
    assert record["attack_goal"] == FALLBACK_GOAL
    with pytest.raises(ValueError, match="suite_name"):
        scorer_record(name, TEST_MEMBERS[name] | {"suite_name": "slack"}, "original_test")
    with pytest.raises(ValueError, match="outside the known"):
        scorer_record(f"{TRAIN}/other/x.json", raw(2, (0, 0)), "original_train")


def test_adapt_release_writes_records_notes_and_manifest(tmp_path):
    spec, source = release(tmp_path)
    manifest = adapt_release(spec, source, tmp_path / "out")
    files = manifest["files"]
    assert files[f"{TRAIN}.tar.gz"]["counts"] == counts(TRAIN_MEMBERS)
    assert files[f"{TEST}.tar.gz"]["counts"] == counts(TEST_MEMBERS)
    assert files[f"{TEST}.tar.gz"]["skipped_members"] == {".yaml": 1}
    assert files[f"{TRAIN}.tar.gz"]["suites"] == {"banking": 2, "slack": 1, "travel": 1}
    assert files[f"{TRAIN}.tar.gz"]["groups"] == 3 and files[f"{TRAIN}.tar.gz"]["total_units_missing"] == 2
    assert files[f"{TRAIN}.tar.gz"]["attack_goal_fallbacks"] == 1
    para = files[f"{PARA}.tar.gz"]
    assert para["counts"]["count_mismatches"] == 1 and len(para["total_units_mismatch_records"]) == 1
    assert para["paraphrase_source_mapping"] == {"matched": 2, "unmatched": 1, "distinct_original_records": 1,
                                                 "source_file_prefixed": 1}
    train = read_jsonl(tmp_path / "out/cad_original_train.jsonl")
    assert [r["record_id"] for r in train] == sorted(r["record_id"] for r in train)
    assert all(validate_record(r, require_split=False) == r for r in train)
    notes = read_jsonl(tmp_path / "out/cad_paraphrased_train.notes.jsonl")
    assert [n["original_record_id"] is not None for n in notes] == [True, True, False]
    assert sha256(tmp_path / "out/cad_original_train.jsonl") == files[f"{TRAIN}.tar.gz"]["records_sha256"]
    written = json.loads((tmp_path / "out/adaptation_manifest.json").read_text(encoding="utf-8"))
    assert written["schema"] == "rag_cad.cad_adaptation/1" and written["cad_commit"] == CAD_COMMIT
    with pytest.raises(FileExistsError):
        adapt_release(spec, source, tmp_path / "out")


def test_adaptation_is_deterministic_and_refuses_count_drift(tmp_path):
    spec, source = release(tmp_path)
    first = adapt_release(spec, source, tmp_path / "one")
    second = adapt_release(spec, source, tmp_path / "two")
    assert first == second
    drifted, _ = release(tmp_path / "drift", train_counts=counts(TRAIN_MEMBERS) | {"rows": 99})
    with pytest.raises(ValueError, match="counts differ"):
        adapt_release(drifted, tmp_path / "drift/release", tmp_path / "three")
    bad_train = TRAIN_MEMBERS | {f"{TRAIN}/agentdojo_banking_scenarios/banking_scenario_0/user_task_3/injection_task_1.json":
                                 raw(5, (1, 1), total_units=9)}
    bad_spec, bad_source = release(tmp_path / "bad", train=bad_train)
    with pytest.raises(ValueError, match="total_units mismatch"):
        adapt_release(bad_spec, bad_source, tmp_path / "four")
    records, notes, extras = adapt_archive(source / f"{PARA}.tar.gz", "paraphrased_train")
    assert len(records) == 3 and sum(n["total_units_mismatch"] for n in notes) == 1 and extras == {"skipped_members": {}}


def test_adapt_cad_cli_runs_without_a_profile(tmp_path, capsys):
    spec, source = release(tmp_path)
    spec_path = tmp_path / "cad_release.yaml"
    spec_path.write_text(yaml.safe_dump(spec), encoding="utf-8")
    assert main(["data", "adapt-cad", "--release", str(spec_path), "--source", str(source),
                 "--output", str(tmp_path / "out"), "--skip-paraphrased"]) == 0
    printed = json.loads(capsys.readouterr().out)
    assert set(printed["files"]) == {f"{TRAIN}.tar.gz", f"{TEST}.tar.gz"}
    assert (tmp_path / "out/cad_original_test.jsonl").is_file()
    assert not (tmp_path / "out/cad_paraphrased_train.jsonl").exists()
    assert main(["data", "adapt-cad", "--release", str(spec_path), "--source", str(source),
                 "--output", str(tmp_path / "out")]) == 2
