import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

from rag_cad.cli import main

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/phase2_families.jsonl"


def prepare(tmp_path):
    experiment = tmp_path / "experiment.yaml"
    experiment.write_text(yaml.safe_dump({"split_ratios": {"train": 0.6, "validation": 0.2, "test": 0.2},
                                          "split_seed": 764, "representation": None}), encoding="utf-8")
    manifest = tmp_path / "split_manifest.json"
    assert main(["data", "split", "--input", str(FIXTURE), "--output", str(manifest),
                 "--experiment", str(experiment)]) == 0
    return str(experiment), str(manifest)


def test_fake_feature_build_and_resume(tmp_path, capsys):
    experiment, manifest = prepare(tmp_path)
    capsys.readouterr()
    root = tmp_path / "features"
    common = ["--input", str(FIXTURE), "--manifest", manifest, "--experiment", experiment, "--output", str(root)]
    assert main(["features", "fake-build", "--condition", "m3_semantic", "--split", "train", *common]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["execution_kind"] == "fake" and result["assembled"]["counts"]["rows"] == 36
    assert (root / "assembled/m3_semantic/train/manifest.json").is_file()
    assert main(["features", "fake-build", "--condition", "m1_random", "--split", "train", *common]) == 2
    assert main(["features", "fake-build", "--condition", "m1_random", "--split", "train", "--resume", *common]) == 0
    assert main(["features", "fake-build", "--condition", "common", "--split", "test", "--resume", *common]) == 0
    assert main(["features", "fake-build", "--condition", "m3_semantic", "--split", "test", "--resume", *common]) == 2
    assert main(["features", "fake-build", "--condition", "m3_semantic", "--split", "train", *common[:-2],
                 "--output", "/content/drive/MyDrive/features"]) == 2


def test_real_feature_build_is_gated_before_any_ml_import(tmp_path):
    experiment, manifest = prepare(tmp_path)
    arguments = ["features", "build", "--condition", "m3_semantic", "--split", "train",
                 "--input", str(FIXTURE), "--manifest", manifest, "--experiment", experiment,
                 "--output", str(tmp_path / "work/features"),
                 "--profile", str(ROOT / "configs/environments/colab_tested.yaml"),
                 "--lock", str(ROOT / "requirements/colab-core.lock.txt"), "--commit", "a" * 40,
                 "--workspace", str(tmp_path / "work"), "--resources", str(tmp_path / "work/nltk"),
                 "--model-bundle", str(tmp_path / "work/bundle")]
    (tmp_path / "work").mkdir()
    assert main(arguments) == 2
    assert main(arguments + ["--execute"]) == 2
    script = ("import sys; from rag_cad.cli import main; "
              f"assert main({arguments + ['--execute']!r}) == 2; "
              "assert not {'torch', 'transformers', 'nltk', 'faiss'} & set(sys.modules)")
    result = subprocess.run([sys.executable, "-c", script], cwd=ROOT,
                            env=os.environ | {"PYTHONPATH": str(ROOT / "src")}, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
