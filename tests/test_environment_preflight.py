from copy import deepcopy

import pytest

from rag_cad.config import validate_profile


@pytest.fixture
def profile():
    return {
        "status": "candidate", "approved": True, "approved_by": "synthetic-test-only",
        "expected": {
            "python": "3.12.10", "packages": {"fake": "1.0"}, "lock_sha256": "a" * 64,
            "gpu_name": "synthetic-device", "gpu_memory_bytes": 16 * 1024**3,
            "cuda": "fake", "driver": "fake", "encoder_revision": "b" * 40,
            "representation": "repo_compatible", "dtype": "float32", "segmenter": "fake",
        },
    }


@pytest.mark.parametrize("stage", ["smoke", "conformance"])
def test_approved_candidate_allowed_only_for_bounded_stages(profile, stage):
    validate_profile(profile, stage, deepcopy(profile["expected"]))


@pytest.mark.parametrize("stage", ["features", "train", "evaluate"])
def test_candidate_rejected_for_final_work(profile, stage):
    with pytest.raises(ValueError, match="tested profile"):
        validate_profile(profile, stage, profile["expected"])


def test_untested_claim_needs_both_runs_and_review(profile):
    profile["status"] = "tested"
    with pytest.raises(ValueError, match="hash"):
        validate_profile(profile, "features", profile["expected"])
    profile["evidence"] = {
        "run_a_manifest_sha256": "c" * 64, "run_b_manifest_sha256": "d" * 64,
        "lock_sha256": "a" * 64, "reviewed_commit": "e" * 40,
    }
    validate_profile(profile, "features", profile["expected"])


def test_unknown_unapproved_and_mismatched_profiles_fail(profile):
    for field, value in [("status", "unknown"), ("approved", False), ("approved_by", None)]:
        broken = deepcopy(profile)
        broken[field] = value
        with pytest.raises(ValueError):
            validate_profile(broken, "smoke", profile["expected"])
    actual = deepcopy(profile["expected"])
    actual["gpu_name"] = "different-device"
    with pytest.raises(ValueError, match="exactly match"):
        validate_profile(profile, "smoke", actual)


def test_small_gpu_and_missing_fingerprint_fail(profile):
    profile["expected"]["gpu_memory_bytes"] = 8 * 1024**3
    with pytest.raises(ValueError, match="exceed"):
        validate_profile(profile, "smoke", profile["expected"])
    del profile["expected"]["encoder_revision"]
    with pytest.raises(ValueError, match="fields"):
        validate_profile(profile, "smoke", profile["expected"])


def test_preflight_checks_commit_cleanliness_and_lock_before_hardware(profile, tmp_path, monkeypatch):
    import importlib

    from rag_cad.operations.provenance import sha256

    operations = importlib.import_module("rag_cad.operations.preflight")
    lock = tmp_path / "dev.lock.txt"
    lock.write_text("synthetic==1.0", encoding="utf-8")
    profile["expected"]["lock_sha256"] = sha256(lock)
    profile["minimum_free_bytes"] = 1
    state = {"commit": "a" * 40, "dirty": ""}

    def git(repo, *args):
        if args[0] == "rev-parse":
            return state["commit"]
        if args[0] == "status":
            return state["dirty"]
        return ""

    monkeypatch.setattr(operations, "git_output", git)
    monkeypatch.setattr(operations, "verify_upstream", lambda repo: {"source_unchanged": True})
    monkeypatch.setattr(operations.subprocess, "run", lambda *args, **kwargs: None)
    result = operations.preflight(tmp_path, "a" * 40, profile, "smoke", lock, tmp_path,
                                  observed=profile["expected"])
    assert result["dirty"] is False
    state["dirty"] = " M changed.py"
    with pytest.raises(ValueError, match="clean"):
        operations.preflight(tmp_path, "a" * 40, profile, "smoke", lock, tmp_path)
    state["dirty"] = ""
    state["commit"] = "b" * 40
    with pytest.raises(ValueError, match="commit"):
        operations.preflight(tmp_path, "a" * 40, profile, "smoke", lock, tmp_path)