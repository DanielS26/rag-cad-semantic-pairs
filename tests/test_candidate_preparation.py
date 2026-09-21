import runpy
from pathlib import Path

import pytest

from rag_cad.config import load_config, validate_profile

ROOT = Path(__file__).resolve().parents[1]


def test_storage_budget_includes_duplicates_dependencies_and_safety():
    script = runpy.run_path(str(ROOT / "scripts/candidate_environment.py"))
    result = script["storage_requirements"](8 * 1024**3, 4 * 1024**3)
    assert result["runtime_free_before_install_bytes"] >= 23 * 1024**3
    assert result["runtime_free_after_install_bytes"] >= 6 * 1024**3
    assert result["drive_free_bytes"] == 128 * 1024**2
    assert result["model_cache_copies"] == 2


def test_committed_linux_lock_matches_evidence_and_candidate():
    import hashlib
    import json

    import yaml

    evidence = json.loads((ROOT / "configs/environments/colab_candidate_cpu_evidence.json").read_text())
    profile = yaml.safe_load((ROOT / "configs/environments/colab_candidate.yaml").read_text())
    lock = (ROOT / "requirements/colab-core.candidate.lock.txt").read_bytes()
    assert b"\r" not in lock
    assert hashlib.sha256(lock).hexdigest() == evidence["lock_sha256"] == profile["expected"]["lock_sha256"]
    assert evidence["gpu_used"] is False and evidence["tested_colab_profile"] is False
    assert profile["status"] == "candidate" and profile["approved"] is True
    assert profile["approved_by"] == "Daniel Song" and profile["proposal_only"] is False
    assert profile["minimum_free_bytes"] == evidence["storage"]["runtime_free_after_install_bytes"]
    assert profile["minimum_free_before_install_bytes"] == evidence["storage"]["runtime_free_before_install_bytes"]
    assert profile["minimum_drive_free_bytes"] == evidence["storage"]["drive_free_bytes"]
    for name, version in profile["expected"]["packages"].items():
        assert evidence["packages"][name] == version


def test_committed_approval_permits_smoke_configuration_only():
    profile = load_config(ROOT / "configs/environments/colab_candidate.yaml")
    validate_profile(profile, "smoke")
    assert profile["status"] == "candidate"
    assert all(value is None for value in profile["evidence"].values())


@pytest.mark.parametrize("stage", ["features", "train", "evaluate"])
def test_committed_smoke_approval_still_blocks_final_stages(stage):
    profile = load_config(ROOT / "configs/environments/colab_candidate.yaml")
    with pytest.raises(ValueError, match="Final stages require a tested profile"):
        validate_profile(profile, stage)

def test_committed_tested_profile_is_frozen_from_both_runs():
    import hashlib

    profile = load_config(ROOT / "configs/environments/colab_tested.yaml")
    candidate = load_config(ROOT / "configs/environments/colab_candidate.yaml")
    tested_lock = (ROOT / "requirements/colab-core.lock.txt").read_bytes()
    assert tested_lock == (ROOT / "requirements/colab-core.candidate.lock.txt").read_bytes()
    assert b"\r" not in tested_lock
    digest = hashlib.sha256(tested_lock).hexdigest()
    assert digest == profile["expected"]["lock_sha256"] == profile["evidence"]["lock_sha256"]
    assert profile["status"] == "tested" and profile["compute_budget_approved"] is False
    assert profile["evidence"]["reviewed_commit"] == "a822b9a032fc3d6c27261b25c62363fc3bc88142"
    assert all(value not in (None, "", {}) for value in profile["expected"].values())
    assert profile["expected"]["packages"] == candidate["expected"]["packages"]
    for key in ("encoder_revision", "encoder_code_revision", "attention", "representation",
                "dtype", "segmenter"):
        assert profile["expected"][key] == candidate["expected"][key]
    assert profile["segmenter_resource"] == candidate["segmenter_resource"]
    assert profile["tolerance"] == candidate["tolerance"]
    for stage in ("smoke", "features", "train", "evaluate"):
        validate_profile(profile, stage, dict(profile["expected"]))
    drifted = dict(profile["expected"]) | {"python": "3.12.14"}
    with pytest.raises(ValueError, match="exactly match"):
        validate_profile(profile, "features", drifted)
    unknown = dict(profile["expected"]) | {"gpu_name": None}
    with pytest.raises(ValueError):
        validate_profile(profile, "features", unknown)
