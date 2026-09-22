import io
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path

from rag_cad.cli import main

ROOT = Path(__file__).resolve().parents[1]


def synthetic_archive(path: Path) -> Path:
    with tarfile.open(path, "w:gz") as handle:
        for name, span in (("banking/s0/a.json", (2, 9)), ("slack/s1/b.json", (0, 1))):
            segments = "\n".join(f"[{index}] Synthetic unit {index}." for index in range(12))
            payload = json.dumps({"user": "Synthetic query.", "sentence_segments": segments,
                                  "injection_span_unit": {"start": span[0], "end": span[1]},
                                  "total_units": 12}).encode()
            member = tarfile.TarInfo(name)
            member.size = len(payload)
            handle.addfile(member, io.BytesIO(payload))
    return path


def test_fake_released_test_command_runs_on_cpu(tmp_path, capsys):
    archive = synthetic_archive(tmp_path / "testing_data_original.tar.gz")
    assert main(["conformance", "fake-released-test", "--archive", str(archive),
                 "--output", str(tmp_path / "out"), "--records", "1"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["execution_kind"] == "fake" and report["records_selected"] == 1 and report["rows"] == 12
    assert set(report["metrics"]) == {"repo_compatible", "paper_exact"}
    assert (tmp_path / "out/released_test_evaluation.json").is_file()
    assert (tmp_path / "out/predictions.jsonl").is_file()
    assert main(["conformance", "fake-released-test", "--archive", str(archive),
                 "--output", str(tmp_path / "out")]) == 2
    assert main(["conformance", "fake-released-test", "--archive", str(archive),
                 "--output", "/content/drive/MyDrive/out"]) == 2


def test_real_released_test_is_gated_before_any_ml_import(tmp_path):
    (tmp_path / "work").mkdir()
    arguments = ["conformance", "released-test", "--profile",
                 str(ROOT / "configs/environments/colab_candidate.yaml"),
                 "--lock", str(ROOT / "requirements/colab-core.candidate.lock.txt"), "--commit", "a" * 40,
                 "--workspace", str(tmp_path / "work"), "--source", str(tmp_path / "work/upstream"),
                 "--resources", str(tmp_path / "work/nltk"), "--model-bundle", str(tmp_path / "work/bundle"),
                 "--output", str(tmp_path / "work/outputs/test"), "--records", "10"]
    assert main(arguments) == 2
    assert main(arguments + ["--execute"]) == 2
    script = ("import sys; from rag_cad.cli import main; "
              f"assert main({arguments + ['--execute']!r}) == 2; "
              "assert not {'torch', 'transformers', 'nltk', 'faiss'} & set(sys.modules)")
    result = subprocess.run([sys.executable, "-c", script], cwd=ROOT,
                            env=os.environ | {"PYTHONPATH": str(ROOT / "src")}, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
