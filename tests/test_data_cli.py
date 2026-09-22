import json
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import yaml

from rag_cad.cli import main
from rag_cad.data.jsonl import read_jsonl, write_jsonl

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/phase2_families.jsonl"
RESOLVED = {"split_ratios": {"train": 0.6, "validation": 0.2, "test": 0.2}, "split_seed": 764,
            "near_duplicate_threshold": 0.6, "benign_length_tolerance": 0.5}


def experiment(tmp_path, **overrides):
    path = tmp_path / "experiment.yaml"
    path.write_text(yaml.safe_dump(RESOLVED | overrides), encoding="utf-8")
    return str(path)


def run(*arguments):
    return main(["data", *arguments])


def test_data_commands_run_end_to_end(tmp_path, capsys):
    config = experiment(tmp_path)
    validate, manifest = tmp_path / "validate.json", tmp_path / "split_manifest.json"
    assert run("validate", "--input", str(FIXTURE), "--output", str(validate), "--experiment", config) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["records"] == 40 and report["roundtrip"] == "not_checked"
    assert report["diagnostics"]["cross_group_near_target_sentences"]["count"] == 0
    assert set(report["input"]["files"]) == {FIXTURE.name}
    assert run("split", "--input", str(FIXTURE), "--output", str(manifest), "--experiment", config) == 0
    written = json.loads(manifest.read_text(encoding="utf-8"))
    assert json.loads(capsys.readouterr().out)["assignments"] == written["assignments"]
    assert written["seed"] == 764 and written["counts"]["train"]["groups"] == 6
    assert run("check-leakage", "--input", str(FIXTURE), "--manifest", str(manifest),
               "--output", str(tmp_path / "leakage.json"), "--experiment", config) == 0
    assert json.loads(capsys.readouterr().out)["leakage_free"] is True
    assert run("compare-budgets", "--input", str(FIXTURE), "--manifest", str(manifest),
               "--output", str(tmp_path / "budget.json"), "--experiment", config) == 0
    budget = json.loads((tmp_path / "budget.json").read_text(encoding="utf-8"))
    assert budget["equal_budget"] and budget["conditions"] == ["m1_random", "m2_keyword", "m3_semantic"]
    assert run("split", "--input", str(FIXTURE), "--output", str(manifest), "--experiment", config) == 2


def test_unresolved_experiment_values_refuse_execution(tmp_path):
    manifest = tmp_path / "manifest.json"
    unresolved = experiment(tmp_path, split_ratios=None)
    assert run("split", "--input", str(FIXTURE), "--output", str(manifest), "--experiment", unresolved) == 2
    assert not manifest.exists()
    assert run("split", "--input", str(FIXTURE), "--output", str(manifest),
               "--experiment", experiment(tmp_path)) == 0
    for key in ("near_duplicate_threshold",):
        assert run("check-leakage", "--input", str(FIXTURE), "--manifest", str(manifest),
                   "--output", str(tmp_path / "leak.json"), "--experiment", experiment(tmp_path, **{key: None})) == 2
    assert run("compare-budgets", "--input", str(FIXTURE), "--manifest", str(manifest),
               "--output", str(tmp_path / "budget.json"),
               "--experiment", experiment(tmp_path, benign_length_tolerance=None)) == 2
    assert not (tmp_path / "leak.json").exists() and not (tmp_path / "budget.json").exists()


def test_roundtrip_flag_requires_profile_and_verified_resources(tmp_path):
    assert run("validate", "--input", str(FIXTURE), "--output", str(tmp_path / "v.json"),
               "--experiment", experiment(tmp_path), "--roundtrip") == 2
    assert not (tmp_path / "v.json").exists()


def test_leakage_failure_still_writes_its_report(tmp_path):
    records = read_jsonl(FIXTURE)
    config = experiment(tmp_path)
    manifest = tmp_path / "manifest.json"
    assert run("split", "--input", str(FIXTURE), "--output", str(manifest), "--experiment", config) == 0
    assignments = json.loads(manifest.read_text(encoding="utf-8"))["assignments"]
    test_group = next(group for group, split in assignments.items() if split == "test")
    train_group = next(group for group, split in assignments.items() if split == "train")
    leaked = deepcopy(records)
    next(record for record in leaked if record["group_id"] == test_group
         and record["condition_source"] == "semantic_benign")["group_id"] = train_group
    write_jsonl(tmp_path / "leaked" / "families.jsonl", leaked)
    leaked_manifest = deepcopy(json.loads(manifest.read_text(encoding="utf-8")))
    (tmp_path / "leaked_manifest.json").write_text(json.dumps(leaked_manifest), encoding="utf-8")
    report = tmp_path / "leakage.json"
    assert run("check-leakage", "--input", str(tmp_path / "leaked"), "--manifest", str(tmp_path / "leaked_manifest.json"),
               "--output", str(report), "--experiment", config) == 2
    written = json.loads(report.read_text(encoding="utf-8"))
    assert written["leakage_free"] is False and written["error_counts"]["families_across_splits"] == 1


def test_data_commands_stay_free_of_ml_imports(tmp_path):
    script = ("import sys; from rag_cad.cli import main; "
              f"main(['data', 'validate', '--input', {str(FIXTURE)!r}, '--output', {str(tmp_path / 'r.json')!r}, "
              f"'--experiment', {experiment(tmp_path)!r}]); "
              "assert not {'torch', 'transformers', 'nltk', 'faiss'} & set(sys.modules)")
    result = subprocess.run([sys.executable, "-c", script], cwd=ROOT,
                            env=os.environ | {"PYTHONPATH": str(ROOT / "src")}, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
