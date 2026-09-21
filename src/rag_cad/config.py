"""Configuration loading and stage-specific environment contracts."""

import re
from pathlib import Path

import yaml

SMOKE_STAGES = {"smoke", "conformance"}
FINAL_STAGES = {"features", "train", "evaluate"}
DISCOVERABLE_FIELDS = {"python", "gpu_name", "gpu_memory_bytes", "cuda", "driver"}


def load_config(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Configuration must be a mapping")
    return value


def require_sha(value: str, length: int = 40) -> str:
    if not isinstance(value, str) or not re.fullmatch(rf"[0-9a-f]{{{length}}}", value):
        raise ValueError(f"Expected an exact {length}-character lowercase hash")
    return value


def validate_profile(profile: dict, stage: str, observed: dict | None = None) -> None:
    if stage not in SMOKE_STAGES | FINAL_STAGES:
        raise ValueError("Unknown execution stage")
    status = profile.get("status")
    if status not in {"candidate", "tested"}:
        raise ValueError("Unknown environment profile status")
    if profile.get("approved") is not True or not profile.get("approved_by"):
        raise ValueError("Environment profile requires explicit researcher approval")
    if profile.get("proposal_only", False):
        raise ValueError("Proposal-only profiles cannot execute")
    if stage in FINAL_STAGES and status != "tested":
        raise ValueError("Final stages require a tested profile")
    if status == "tested":
        evidence = profile.get("evidence", {})
        for key in ("run_a_manifest_sha256", "run_b_manifest_sha256", "lock_sha256"):
            require_sha(evidence.get(key), 64)
        require_sha(evidence.get("reviewed_commit"))
    expected = profile.get("expected")
    if not isinstance(expected, dict) or not expected:
        raise ValueError("Profile has unresolved expected environment values")
    required = {
        "python", "packages", "lock_sha256", "gpu_name", "gpu_memory_bytes",
        "cuda", "driver", "encoder_revision", "encoder_code_revision", "attention",
        "representation", "dtype", "segmenter",
    }
    if set(expected) != required or (observed is not None and set(observed) != required):
        raise ValueError("Environment fingerprint fields are missing or unknown")
    discovery = status == "candidate" and stage in SMOKE_STAGES
    for key, value in expected.items():
        if discovery and key in DISCOVERABLE_FIELDS and value is None:
            continue
        if value is None or value == "" or value == {}:
            raise ValueError(f"Unresolved environment field: {key}")
    require_sha(expected["encoder_revision"])
    require_sha(expected["encoder_code_revision"])
    require_sha(expected["lock_sha256"], 64)
    if expected["representation"] not in {"repo_compatible", "paper_exact"}:
        raise ValueError("Unknown representation")
    if expected["dtype"] != "float32":
        raise ValueError("Only the contracted float32 profile is supported")
    if expected["attention"] != "native":
        raise ValueError("This candidate loader supports explicit native attention only")
    if not isinstance(expected["packages"], dict):
        raise ValueError("Expected exact package versions")
    if status == "tested" and profile["evidence"]["lock_sha256"] != expected["lock_sha256"]:
        raise ValueError("Tested evidence and runtime lock hashes differ")
    if observed is None:
        return
    for key, value in observed.items():
        if value is None or value == "" or value == {}:
            raise ValueError(f"Missing measured environment field: {key}")
        if not (discovery and key in DISCOVERABLE_FIELDS and expected[key] is None):
            if value != expected[key]:
                raise ValueError("Runtime does not exactly match the approved environment profile")
    memory = observed["gpu_memory_bytes"]
    if type(memory) is not int or memory <= 8 * 1024**3:
        raise ValueError("Measured GPU memory must exceed 8 GiB")
    if not isinstance(observed["gpu_name"], str) or not observed["gpu_name"].strip():
        raise ValueError("Missing measured GPU name")
    if not re.fullmatch(r"3\.13\.\d+", observed["python"]):
        raise ValueError("Candidate lock requires Python 3.13.x")