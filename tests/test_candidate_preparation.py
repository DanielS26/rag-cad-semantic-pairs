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