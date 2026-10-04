import json
from pathlib import Path

import yaml
from cad_release_fixture import release

from rag_cad.cli import main
from rag_cad.data.jsonl import read_jsonl
from rag_cad.operations import smoke

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = str(ROOT / "configs/experiment.yaml")
STEPS = ["d0_adapted", "d0_split_assigned", "m0_train_features_built", "m0_test_features_built",
         "m0_trained", "m0_evaluated", "phase4_report_written"]


def test_fake_phase4_run_adapts_splits_builds_trains_and_evaluates(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(smoke, "PROGRESS_PATH", tmp_path / "progress.json")
    spec, source = release(tmp_path)
    spec_path = tmp_path / "cad_release.yaml"
    spec_path.write_text(yaml.safe_dump(spec), encoding="utf-8")
    output = tmp_path / "phase4"
    common = ["m0", "fake-run", "--release", str(spec_path), "--source", str(source), "--experiment", EXPERIMENT]
    assert main(common + ["--output", str(output)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["execution_kind"] == "fake" and report["stage"] == "phase4_m0" and report["seeds"] == [0, 1, 2]
    assert report["split"]["d0_holdout_policy"] == "none" and report["split"]["pinned_groups"] == 6
    assert report["split"]["counts"]["train"]["groups"] == 3 and report["split"]["counts"]["test"]["groups"] == 3
    assert report["split"]["counts"]["validation"]["groups"] == 0
    assert report["features"]["train"]["counts"]["rows"] == 18 and report["features"]["test"]["counts"]["rows"] == 12
    assert report["adaptation"]["testing_data_original.tar.gz"]["counts"]["records"] == 3
    assert set(report["models"]) == {"0", "1", "2"} and report["aggregate"]["all_rows_roc_auc"]["seeds"] == 3
    assert report["reference_checkpoint"]["rows"] == 12 and report["upstream_split_leakage"]["refused"] is True
    assert report["recipe"]["epochs"] == 30 and report["maximum_token_length"] > 0
    for seed in (0, 1, 2):
        directory = output / "models/m0_base" / f"seed_{seed}"
        assert {path.name for path in directory.iterdir()} == {"model.json", "config.resolved.yaml",
                                                               "train_manifest.json", "run_metadata.json",
                                                               "test_predictions.jsonl"}
        metadata = json.loads((directory / "run_metadata.json").read_text(encoding="utf-8"))
        assert metadata["condition"] == "m0_base" and metadata["seed"] == seed
        assert metadata["dataset_manifest_sha256"] == report["split"]["manifest_sha256"]
        assert metadata["checkpoint_sha256"] == report["models"][str(seed)]["checkpoint_sha256"]
        assert len(read_jsonl(directory / "test_predictions.jsonl")) == 12
        resolved = yaml.safe_load((directory / "config.resolved.yaml").read_text(encoding="utf-8"))
        assert resolved["training"]["epochs"] == 30 and resolved["representation"] == "repo_compatible"
    assert json.loads((tmp_path / "progress.json").read_text(encoding="utf-8")) == STEPS
    assert (output / "adapted/cad_original_train.jsonl").is_file() and (output / "split_manifest.json").is_file()
    assert (output / "reference_checkpoint_test_predictions.jsonl").is_file()
    assert main(common + ["--output", str(output)]) == 2
    assert main(common + ["--output", str(tmp_path / "one_seed"), "--seeds", "1"]) == 0
    assert set(json.loads(capsys.readouterr().out)["models"]) == {"1"}
    assert main(common + ["--output", str(tmp_path / "bad_seed"), "--seeds", "5"]) == 2


def test_real_phase4_run_is_gated_behind_the_tested_profile(tmp_path):
    spec, source = release(tmp_path)
    spec_path = tmp_path / "cad_release.yaml"
    spec_path.write_text(yaml.safe_dump(spec), encoding="utf-8")
    (tmp_path / "work").mkdir()
    arguments = ["m0", "run", "--release", str(spec_path), "--source", str(source),
                 "--output", str(tmp_path / "work/phase4"), "--experiment", EXPERIMENT,
                 "--profile", str(ROOT / "configs/environments/colab_candidate.yaml"),
                 "--lock", str(ROOT / "requirements/colab-core.candidate.lock.txt"), "--commit", "a" * 40,
                 "--workspace", str(tmp_path / "work"), "--resources", str(tmp_path / "work/nltk"),
                 "--model-bundle", str(tmp_path / "work/bundle")]
    assert main(arguments) == 2
    assert main(arguments + ["--execute"]) == 2
