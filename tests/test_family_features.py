"""Phase 6 preparation for the family encoder run: all-train manifest, family stage, readiness check."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from rag_cad.cad.representation import RepresentationConfig
from rag_cad.cli import main
from rag_cad.data.jsonl import load_records, read_jsonl, write_jsonl
from rag_cad.data.split import apply_manifest, assign_all_train
from rag_cad.operations.family_features import check_reference, load_reference

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = ROOT / "datasets/raw/augmentation/families"
ALL_TRAIN = ROOT / "datasets/raw/augmentation/split_all_train_v1.json"
PENDING = ROOT / "datasets/raw/augmentation/review/encoder_pending_v1.txt"
FOLDS = ROOT / "datasets/raw/augmentation/folds_v1.jsonl"
REFERENCE = ROOT / "configs/phase6/phase4_feature_identity.json"
FIXTURE = ROOT / "tests/fixtures/phase2_families.jsonl"


def test_all_train_split_flag_and_refusal(tmp_path, capsys):
    config = tmp_path / "e.yaml"
    config.write_text(yaml.safe_dump({"split_ratios": None, "split_seed": 764, "d0_holdout_policy": "none"}),
                      encoding="utf-8")
    output = tmp_path / "m.json"
    assert main(["data", "split", "--all-train", "--input", str(FIXTURE), "--output", str(output),
                 "--experiment", str(config)]) == 0
    manifest = json.loads(output.read_text(encoding="utf-8"))
    assert manifest["mode"] == "all_train" and set(manifest["assignments"].values()) == {"train"}
    assert manifest["counts"]["test"]["records"] == 0 and manifest["counts"]["validation"]["records"] == 0
    assert main(["data", "split", "--input", str(FIXTURE), "--output", str(tmp_path / "n.json"),
                 "--experiment", str(config)]) == 2
    records, _ = load_records(FIXTURE)
    pinned = [{**record, "condition_source": "test_only"} if index == 0 else record
              for index, record in enumerate(records)]
    with pytest.raises(ValueError, match="pinned to test"):
        assign_all_train(pinned)
    capsys.readouterr()


def test_tracked_all_train_manifest_is_reproducible(tmp_path):
    records, _ = load_records(FAMILIES)
    assigned = apply_manifest(records, json.loads(ALL_TRAIN.read_text(encoding="utf-8")))
    assert len(assigned) == 800 and {record["split"] for record in assigned} == {"train"}
    output = tmp_path / "m.json"
    assert main(["data", "split", "--all-train", "--input", str(FAMILIES), "--output", str(output)]) == 0
    assert output.read_bytes() == ALL_TRAIN.read_bytes()


def test_tested_profile_reproduces_the_phase4_identity():
    reference = load_reference(REFERENCE)
    profile = yaml.safe_load((ROOT / "configs/environments/colab_tested.yaml").read_text(encoding="utf-8"))
    representation = RepresentationConfig.from_profile(profile, mode="repo_compatible")
    identity = {**reference["identity"], "representation_id": representation.representation_id,
                "encoder_revision": representation.encoder_revision,
                "encoder_code_revision": representation.encoder_code_revision,
                "segmenter": representation.segmenter, "dtype": representation.dtype, "commit": "f" * 40}
    check = check_reference(identity, reference)
    assert check["matches"] and check["informational"]["commit"]["same"] is False
    changed = check_reference({**identity, "encoder_code_revision": "0" * 40}, reference)
    assert not changed["matches"] and set(changed["differences"]) == {"encoder_code_revision"}
    assert changed["message"].startswith("STOP")


def _subset(tmp_path, ids):
    pending = tmp_path / "p.txt"
    pending.write_text("".join(f"{record_id}\n" for record_id in sorted(ids)), encoding="utf-8")
    groups = {f"unit_{record_id.rsplit('_', 1)[0]}" for record_id in ids}
    folds = tmp_path / "f.jsonl"
    write_jsonl(folds, [row for row in read_jsonl(FOLDS) if row["group_id"] in groups])
    return pending, folds


def test_fake_family_stage_end_to_end_and_readiness(tmp_path, capsys):
    out = tmp_path / "o"
    common = ["--input", str(FAMILIES), "--split-manifest", str(ALL_TRAIN)]
    assert main(["features", "fake-build-families", *common, "--output", str(out), "--groups", "3"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["records"] == 12 and report["groups"] == 3
    assert report["encoder_passes"] == report["expected_passes_one_set"] == 12 + 2 * report["sentences"]
    assert set(report["modes"]) == {"repo_compatible", "paper_exact"}
    for mode in report["modes"].values():
        assert set(mode["shards"]) == {"shared_malicious", "random_benign", "keyword_benign", "semantic_benign"}
        assert set(mode["assembled"]) == {"m1_random", "m2_keyword", "m3_semantic"}
    assert report["identity_check"] is None
    # never over an existing directory
    assert main(["features", "fake-build-families", *common, "--output", str(out), "--groups", "3"]) == 2
    ids = [row["record_id"] for row in read_jsonl(next((out / "features/repo_compatible/shards").glob("*/*"))
                                                  / "rows.jsonl")]
    selected = sorted({line for line in PENDING.read_text(encoding="utf-8").split()
                       if line.rsplit("_", 1)[0] in {"pilot_0001", "pilot_0002", "pilot_0003"}})
    assert set(ids) <= set(selected) and len(selected) == 12
    pending, folds = _subset(tmp_path, selected)
    check = ["features", "check-families", "--features", str(out), "--input", str(FAMILIES),
             "--pending", str(pending), "--folds", str(folds)]
    assert main([*check, "--skip-reference", "--output", str(tmp_path / "r.json")]) == 0
    ready = json.loads(capsys.readouterr().out)
    assert ready["ready"] and ready["join_field"] == "group_id"
    m1 = ready["modes"]["repo_compatible"]["assembled"]["m1_random"]
    assert m1["rows_with_null_family_id"] > 0
    for counts in m1["rounds"].values():
        assert counts["training_families"] + counts["held_out_families"] == 3
    # the real reference refuses synthetic identities; a missing shard is not ready
    assert main([*check, "--output", str(tmp_path / "s.json")]) == 2
    shutil.rmtree(next((out / "features/paper_exact/shards/semantic_benign").iterdir()))
    assert main([*check, "--skip-reference", "--output", str(tmp_path / "t.json")]) == 2
    failed = json.loads((tmp_path / "t.json").read_text(encoding="utf-8"))
    assert any(error.startswith("paper_exact: coverage missing 3") for error in failed["errors"])
    # the full pending list does not match a three-group build
    assert main(["features", "check-families", "--features", str(out), "--input", str(FAMILIES),
                 "--skip-reference", "--output", str(tmp_path / "u.json")]) == 2
    capsys.readouterr()


def test_family_stage_stops_on_identity_mismatch_before_encoding(tmp_path, capsys):
    out = tmp_path / "o"
    assert main(["features", "fake-build-families", "--input", str(FAMILIES), "--split-manifest", str(ALL_TRAIN),
                 "--output", str(out), "--groups", "1", "--reference", str(REFERENCE)]) == 2
    check = json.loads((out / "identity_check.json").read_text(encoding="utf-8"))
    assert not check["matches"] and "encoder_revision" in check["differences"]
    assert not (out / "features").exists()
    # a manifest that is not all-train is refused
    split = tmp_path / "s.json"
    split.write_text(json.dumps({**json.loads(ALL_TRAIN.read_text(encoding="utf-8")),
                                 "assignments": {group: "test" for group in json.loads(
                                     ALL_TRAIN.read_text(encoding="utf-8"))["assignments"]}}), encoding="utf-8")
    assert main(["features", "fake-build-families", "--input", str(FAMILIES), "--split-manifest", str(split),
                 "--output", str(tmp_path / "p"), "--groups", "1"]) == 2
    capsys.readouterr()


def test_real_family_stage_is_gated_before_any_ml_import(tmp_path):
    (tmp_path / "w").mkdir()
    arguments = ["features", "build-families", "--input", str(FAMILIES), "--split-manifest", str(ALL_TRAIN),
                 "--output", str(tmp_path / "w/out"),
                 "--profile", str(ROOT / "configs/environments/colab_tested.yaml"),
                 "--lock", str(ROOT / "requirements/colab-core.lock.txt"), "--commit", "a" * 40,
                 "--workspace", str(tmp_path / "w"), "--resources", str(tmp_path / "w/nltk"),
                 "--model-bundle", str(tmp_path / "w/bundle"), "--execute"]
    script = ("import sys; from rag_cad.cli import main; "
              f"assert main({arguments!r}) == 2; "
              "assert not {'torch', 'transformers', 'nltk', 'faiss'} & set(sys.modules)")
    result = subprocess.run([sys.executable, "-c", script], cwd=ROOT,
                            env=os.environ | {"PYTHONPATH": str(ROOT / "src")}, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert not (tmp_path / "w/out").exists()
