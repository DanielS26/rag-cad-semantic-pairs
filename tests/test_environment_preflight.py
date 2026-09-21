from copy import deepcopy

import pytest

from rag_cad.config import validate_profile


@pytest.fixture
def profile():
    return {
        "status": "candidate", "approved": True, "approved_by": "synthetic-test-only",
        "expected": {
            "python": "3.13.15", "packages": {"fake": "1.0"}, "lock_sha256": "a" * 64,
            "gpu_name": "synthetic-device", "gpu_memory_bytes": 16 * 1024**3,
            "cuda": "fake", "driver": "fake", "encoder_revision": "b" * 40,
            "encoder_code_revision": "c" * 40, "attention": "native",
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


def test_proposals_and_missing_code_pin_fail_even_with_approval_flag(profile):
    with pytest.raises(ValueError, match="Proposal-only"):
        validate_profile(profile | {"proposal_only": True}, "smoke", profile["expected"])
    del profile["expected"]["encoder_code_revision"]
    with pytest.raises(ValueError, match="fields"):
        validate_profile(profile, "smoke", profile["expected"])


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


def test_candidate_discovers_only_runtime_fields_without_mutation(profile):
    from rag_cad.config import DISCOVERABLE_FIELDS

    actual = deepcopy(profile["expected"])
    for key in DISCOVERABLE_FIELDS:
        profile["expected"][key] = None
    before = deepcopy(profile)
    validate_profile(profile, "smoke")
    validate_profile(profile, "smoke", actual)
    assert profile == before
    for stage in ("features", "train", "evaluate"):
        with pytest.raises(ValueError, match="tested profile"):
            validate_profile(profile, stage, actual)
    profile["expected"]["encoder_revision"] = None
    with pytest.raises(ValueError, match="Unresolved"):
        validate_profile(profile, "smoke", actual)


@pytest.mark.parametrize("field,value", [("gpu_memory_bytes", 8 * 1024**3),
    ("gpu_memory_bytes", 0), ("gpu_memory_bytes", True), ("driver", None),
    ("cuda", ""), ("gpu_name", ""), ("python", "3.12.14")])
def test_bad_discovered_runtime_fails(profile, field, value):
    from rag_cad.config import DISCOVERABLE_FIELDS

    actual = deepcopy(profile["expected"])
    for key in DISCOVERABLE_FIELDS:
        profile["expected"][key] = None
    actual[field] = value
    with pytest.raises(ValueError):
        validate_profile(profile, "smoke", actual)


def test_measured_dependencies_cannot_be_discovered_away(profile):
    actual = deepcopy(profile["expected"])
    actual["packages"] = {"fake": "2.0"}
    with pytest.raises(ValueError, match="exactly match"):
        validate_profile(profile, "smoke", actual)


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


@pytest.fixture
def discovery_gate(profile, tmp_path, monkeypatch):
    import importlib
    import sys
    from types import SimpleNamespace

    from rag_cad.config import DISCOVERABLE_FIELDS
    from rag_cad.operations.provenance import sha256

    operations = importlib.import_module("rag_cad.operations.preflight")
    lock = tmp_path / "candidate.lock.txt"
    lock.write_text("fake==1.0", encoding="utf-8")
    profile["expected"]["lock_sha256"] = sha256(lock)
    profile["minimum_free_bytes"] = 1
    actual = deepcopy(profile["expected"])
    for key in DISCOVERABLE_FIELDS:
        profile["expected"][key] = None
    monkeypatch.setattr(operations, "git_output", lambda repo, *args: "a" * 40 if args[0] == "rev-parse" else "")
    monkeypatch.setattr(operations, "verify_upstream", lambda repo: {"source_unchanged": True})
    monkeypatch.setattr(operations, "observe_environment", lambda *args: actual)
    monkeypatch.setattr(operations, "verify_lock_packages", lambda lock: {"fake": "1.0"})
    monkeypatch.setattr(operations.subprocess, "run", lambda *args, **kwargs: None)

    class Tensor:
        def __add__(self, value):
            return self

        def item(self):
            return 2

    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(ones=lambda *args, **kwargs: Tensor()))
    return operations, profile, actual, lock, tmp_path


def test_discovery_precedes_matching_and_records_actual_runtime(discovery_gate):
    operations, profile, actual, lock, work = discovery_gate
    before = deepcopy(profile)
    report = operations.preflight(work, "a" * 40, profile, "smoke", lock, work)
    assert report["passed"] and report["environment"] == actual
    assert report["environment_id"] and profile == before


@pytest.mark.parametrize("field,value", [("gpu_memory_bytes", 8 * 1024**3), ("cuda", None),
                                       ("driver", ""), ("packages", {"wrong": "1"})])
def test_failed_discovery_keeps_measurements(discovery_gate, field, value):
    operations, profile, actual, lock, work = discovery_gate
    actual[field] = value
    with pytest.raises(operations.PreflightError) as error:
        operations.preflight(work, "a" * 40, profile, "smoke", lock, work)
    assert error.value.report["passed"] is False
    assert error.value.report["environment"][field] == value


@pytest.mark.parametrize("failure", ["no_gpu", "driver", "allocation", "pip"])
def test_runtime_failures_abort_with_safe_report(discovery_gate, monkeypatch, failure):
    import subprocess
    import sys

    operations, profile, actual, lock, work = discovery_gate

    def fail(*args, **kwargs):
        if failure == "no_gpu":
            raise ValueError("GPU stage requires CUDA")
        if failure in {"driver", "pip"}:
            raise subprocess.CalledProcessError(1, "synthetic-command")
        raise RuntimeError("synthetic GPU allocation failed")

    if failure in {"no_gpu", "driver"}:
        monkeypatch.setattr(operations, "observe_environment", fail)
    elif failure == "allocation":
        monkeypatch.setattr(sys.modules["torch"], "ones", fail)
    else:
        monkeypatch.setattr(operations.subprocess, "run", fail)
    with pytest.raises(operations.PreflightError):
        operations.preflight(work, "a" * 40, profile, "smoke", lock, work)


def test_tested_profiles_never_discover_unknowns(profile):
    profile["status"] = "tested"
    profile["evidence"] = {"run_a_manifest_sha256": "a" * 64, "run_b_manifest_sha256": "b" * 64,
                           "lock_sha256": "a" * 64, "reviewed_commit": "c" * 40}
    actual = deepcopy(profile["expected"])
    profile["expected"]["gpu_name"] = None
    for stage in ("smoke", "features", "train", "evaluate"):
        with pytest.raises(ValueError, match="Unresolved"):
            validate_profile(profile, stage, actual)


def test_observer_records_device_zero_and_rejects_no_cuda_or_driver(profile, tmp_path, monkeypatch):
    import importlib
    import sys
    from types import SimpleNamespace

    operations = importlib.import_module("rag_cad.operations.preflight")
    lock = tmp_path / "lock"
    lock.write_text("fake==1", encoding="utf-8")
    cuda = SimpleNamespace(is_available=lambda: True,
                           get_device_properties=lambda index: SimpleNamespace(name="NVIDIA synthetic", total_memory=16 * 1024**3))
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(cuda=cuda, version=SimpleNamespace(cuda="12.8")))
    monkeypatch.setattr(operations.importlib.metadata, "version", lambda name: "synthetic-version")
    calls = []

    def command(args, **kwargs):
        calls.append(args)
        return SimpleNamespace(stdout="synthetic-driver\n")

    monkeypatch.setattr(operations.subprocess, "run", command)
    observed = operations.observe_environment(profile, lock)
    assert observed["gpu_memory_bytes"] == 16 * 1024**3 and observed["cuda"] == "12.8"
    assert "--id=0" in calls[0]
    monkeypatch.setattr(operations.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(stdout=""))
    with pytest.raises(ValueError, match="driver"):
        operations.observe_environment(profile, lock)
    cuda.is_available = lambda: False
    with pytest.raises(ValueError, match="CUDA"):
        operations.observe_environment(profile, lock)


def test_complete_lock_versions_checked(tmp_path, monkeypatch):
    import importlib

    operations = importlib.import_module("rag_cad.operations.preflight")
    lock = tmp_path / "candidate.lock.txt"
    lock.write_text("fake==1.0\n", encoding="utf-8")
    monkeypatch.setattr(operations.importlib.metadata, "version", lambda name: "1.0")
    assert operations.verify_lock_packages(lock) == {"fake": "1.0"}
    monkeypatch.setattr(operations.importlib.metadata, "version", lambda name: "2.0")
    with pytest.raises(ValueError, match="differs"):
        operations.verify_lock_packages(lock)
    for text in ("fake>=1.0", "", "fake==1.0\nfake==1.0\n"):
        lock.write_text(text, encoding="utf-8")
        with pytest.raises(ValueError):
            operations.verify_lock_packages(lock)


def test_missing_locked_package_and_insufficient_disk_fail(discovery_gate, monkeypatch):
    import importlib.metadata
    from types import SimpleNamespace

    operations, profile, actual, lock, work = discovery_gate

    def missing(path):
        raise importlib.metadata.PackageNotFoundError("synthetic")

    monkeypatch.setattr(operations, "verify_lock_packages", missing)
    with pytest.raises(operations.PreflightError) as error:
        operations.preflight(work, "a" * 40, profile, "smoke", lock, work)
    assert error.value.report["environment"] == actual
    monkeypatch.setattr(operations.shutil, "disk_usage", lambda path: SimpleNamespace(free=0))
    with pytest.raises(ValueError, match="disk"):
        operations.preflight(work, "a" * 40, profile, "smoke", lock, work)