"""Synthetic CAD release archives in the real layout, shared by the adapter and Phase 4 tests."""

import io
import json
import tarfile
from pathlib import Path

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
    """A complete release specification and source directory for the synthetic archives."""
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
