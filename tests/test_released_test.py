import io
import json
import tarfile
from pathlib import Path

import numpy as np
import pytest

from rag_cad.data.jsonl import read_jsonl
from rag_cad.operations import smoke
from rag_cad.operations.released_test import (
    evaluate_released_test,
    load_released_test,
    record_domain,
)
from rag_cad.operations.smoke import FakeBackend

ROOT = "testing_data_original"
RECORDS = {
    f"{ROOT}/slack/scenario_1/task_b.json": {"user": "Summarise the channel.", "span": (3, 4), "units": 6},
    f"{ROOT}/banking/scenario_0/task_a.json": {"user": "List my transactions.", "span": (2, 9), "units": 12},
    f"{ROOT}/travel/scenario_2/task_c.json": {"user": "Book a hotel.", "span": (0, 0), "units": 4},
}


def archive(tmp_path: Path, records: dict = RECORDS) -> Path:
    path = tmp_path / "testing_data_original.tar.gz"
    with tarfile.open(path, "w:gz") as handle:
        for name, spec in records.items():
            segments = "\n".join(f"[{index}] Synthetic sentence number {index} for {name}."
                                 for index in range(spec["units"]))
            payload = json.dumps({"user": spec["user"], "sentence_segments": segments,
                                  "injection_span_unit": {"start": spec["span"][0], "end": spec["span"][1]},
                                  "total_units": spec["units"]}).encode()
            member = tarfile.TarInfo(name)
            member.size = len(payload)
            handle.addfile(member, io.BytesIO(payload))
    return path


def test_records_load_in_sorted_order_with_domains_and_masks(tmp_path):
    records = load_released_test(archive(tmp_path))
    assert [record["source_file"] for record in records] == sorted(RECORDS)
    assert [record["domain"] for record in records] == ["banking", "slack", "travel"]
    banking = records[0]
    assert banking["labels"] == [0, 0] + [1] * 8 + [0, 0] and banking["span"] == [2, 9]
    assert banking["upstream_mask"] == [True, True] + [False] * 8 + [True, True]
    slack = records[1]
    assert slack["labels"] == [0, 0, 0, 1, 1, 0] and slack["upstream_mask"] == [True, True, True, False, False, True]


def test_domain_is_the_first_directory_under_the_extracted_test_folder():
    """Upstream build_eval_mask takes the first path component relative to the test directory."""
    assert record_domain(f"{ROOT}/banking/banking_scenario_0/injection_task_1.json") == "banking"
    assert record_domain("travel/scenario_2/task_c.json") == "travel"
    assert record_domain(f"{ROOT}/loose.json") == "unknown"
    assert record_domain("loose.json") == "unknown"


def test_fake_evaluation_reports_both_modes_with_masked_and_unmasked_metrics(tmp_path, monkeypatch):
    monkeypatch.setattr(smoke, "PROGRESS_PATH", tmp_path / "progress.json")
    source = archive(tmp_path)
    report = evaluate_released_test(FakeBackend(), source, tmp_path / "out",
                                    {"synthetic_only": True}, "fake-runtime")
    assert report["execution_kind"] == "fake" and report["records_scored"] == 3 and report["rows"] == 22
    assert report["positives"] == 11 and report["masked_out_malicious"] == 11 and report["masked_out_rows"] == 11
    assert report["domains"] == {"banking": 12, "slack": 6, "travel": 4}
    assert set(report["metrics"]) == {"repo_compatible", "paper_exact"}
    for mode in report["metrics"].values():
        assert mode["all_rows"]["rows"] == 22 and mode["upstream_masked"]["rows"] == 11
        assert mode["upstream_masked"]["positives"] == 0 and mode["upstream_masked"]["average_precision"] is None
        assert set(mode["by_domain_masked"]) == {"banking", "slack", "travel"}
        assert mode["all_rows"]["roc_auc"] is not None
    assert report["timings_seconds"]["encode_both_modes"] >= 0 and report["encoder_passes"] == 3 + 2 * 22
    assert report["comparison"]["primary_mode_selected"] is False
    assert report["comparison"]["higher_masked_average_precision"] is None
    assert 0 <= report["comparison"]["decision_agreement_rate"] <= 1
    rows = read_jsonl(tmp_path / "out/predictions.jsonl")
    assert len(rows) == 22 and rows[0]["source_file"].startswith(f"{ROOT}/banking/")
    assert all(0 <= row["p_repo_compatible"] <= 1 and 0 <= row["p_paper_exact"] <= 1 for row in rows)
    assert json.loads((tmp_path / "progress.json").read_text()) == [
        "released_test_extracted", "released_test_encoded", "released_test_scored", "released_test_report_written"]
    written = json.loads((tmp_path / "out/released_test_evaluation.json").read_text(encoding="utf-8"))
    assert written["rows"] == 22 and written["oracle"].startswith("none published")
    with pytest.raises(FileExistsError):
        evaluate_released_test(FakeBackend(), source, tmp_path / "out", {}, "fake")


def test_record_limit_domain_filter_and_over_length_skips(tmp_path):
    source = archive(tmp_path)
    pilot = evaluate_released_test(FakeBackend(), source, tmp_path / "pilot", {}, "fake", records=1)
    assert pilot["records_selected"] == 1 and pilot["domains"] == {"banking": 12}
    travel = evaluate_released_test(FakeBackend(), source, tmp_path / "travel", {}, "fake", domains=("travel",))
    assert travel["records_selected"] == 1 and travel["rows"] == 4
    with pytest.raises(ValueError, match="No released test records"):
        evaluate_released_test(FakeBackend(), source, tmp_path / "none", {}, "fake", domains=("github",))
    with pytest.raises(ValueError, match="non-negative"):
        evaluate_released_test(FakeBackend(), source, tmp_path / "bad", {}, "fake", records=-1)

    class LimitedEncoder:
        def __init__(self, inner):
            self.inner = inner

        @property
        def max_token_length(self):
            return self.inner.max_token_length

        def __call__(self, text):
            if "task_c" in text:
                raise ValueError("Smoke input exceeds encoder token limit; no silent truncation")
            return self.inner(text)

    class Limited(FakeBackend):
        def __init__(self):
            super().__init__()
            self.encoder = LimitedEncoder(self.encoder)

    limited = evaluate_released_test(Limited(), source, tmp_path / "limited", {}, "fake")
    assert limited["skipped_over_length"] == [f"{ROOT}/travel/scenario_2/task_c.json"]
    assert limited["records_scored"] == 2 and limited["rows"] == 18


def test_comparison_identifies_the_mode_the_checkpoint_fits(tmp_path):
    source = archive(tmp_path, {"banking/s/a.json": {"user": "Q.", "span": (0, 15), "units": 20},
                                "slack/s/b.json": {"user": "Q.", "span": (2, 13), "units": 16}})
    labels = [np.array(record["labels"], dtype=float) for record in load_released_test(source)]

    class Scripted(FakeBackend):
        """First reference call per record is repo_compatible (fits the labels), second is
        paper_exact (anti-fits), mirroring a checkpoint trained on one recipe."""

        calls = 0

        def reference_score(self, features):
            record, fits = labels[self.calls // 2], self.calls % 2 == 0
            self.calls += 1
            positive = 0.9 * record + 0.05 if fits else 0.9 * (1 - record) + 0.05
            return np.column_stack([1 - positive, positive])

    report = evaluate_released_test(Scripted(), source, tmp_path / "out", {}, "fake")
    assert report["positives"] == 28 and report["masked_out_malicious"] == 16
    comparison = report["comparison"]
    assert comparison["masked_roc_auc"] == {"repo_compatible": 1.0, "paper_exact": 0.0}
    assert comparison["masked_average_precision"]["repo_compatible"] == 1.0
    assert comparison["higher_masked_average_precision"] == "repo_compatible"
    assert comparison["decision_agreement_rate"] == 0.0 and comparison["primary_mode_selected"] is False
    banking = report["metrics"]["repo_compatible"]["by_domain_masked"]["banking"]
    assert banking["rows"] == 12 and banking["positives"] == 8 and banking["at_threshold_inclusive"]["tp"] == 8
