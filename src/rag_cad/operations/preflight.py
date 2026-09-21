"""Fail-closed preflight; inspecting real hardware is separate from CPU tests."""

import importlib.metadata
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from rag_cad.config import require_sha, validate_profile
from rag_cad.operations.paths import local_path
from rag_cad.operations.provenance import (
    digest,
    git_output,
    reject_secrets,
    sha256,
    verify_upstream,
)

PACKAGES = ("torch", "transformers", "numpy", "nltk", "scikit-learn", "faiss-cpu",
            "huggingface-hub", "einops", "sentencepiece")


class PreflightError(ValueError):
    def __init__(self, message: str, report: dict):
        super().__init__(message)
        self.report = report | {"passed": False, "failure": message}


def observe_environment(profile: dict, lock: Path) -> dict:
    import torch

    if not torch.cuda.is_available():
        raise ValueError("GPU stage requires CUDA; stop before loading Jina")
    properties = torch.cuda.get_device_properties(0)
    driver = subprocess.run(
        ["nvidia-smi", "--id=0", "--query-gpu=driver_version", "--format=csv,noheader"],
        check=True, capture_output=True, text=True, timeout=15,
    ).stdout.splitlines()[0].strip()
    return {
        "python": platform.python_version(),
        "packages": {name: importlib.metadata.version(name) for name in PACKAGES},
        "lock_sha256": sha256(lock), "gpu_name": properties.name,
        "gpu_memory_bytes": properties.total_memory, "cuda": torch.version.cuda,
        "driver": driver, "encoder_revision": profile["expected"]["encoder_revision"],
        "encoder_code_revision": profile["expected"]["encoder_code_revision"],
        "attention": "native",
        "representation": profile["expected"]["representation"],
        "dtype": "float32", "segmenter": profile["expected"]["segmenter"],
    }


def preflight(repo: Path, commit: str, profile: dict, stage: str, lock: Path,
              workspace: Path, observed: dict | None = None) -> dict:
    require_sha(commit)
    reject_secrets(profile)
    validate_profile(profile, stage)
    if git_output(repo, "rev-parse", "HEAD") != commit:
        raise ValueError("Checked-out commit differs from requested exact commit")
    if git_output(repo, "status", "--porcelain", "--untracked-files=all"):
        raise ValueError("Execution requires a clean worktree")
    upstream = verify_upstream(repo)
    if profile["status"] == "tested":
        tested_commit = profile["evidence"]["reviewed_commit"]
        git_output(repo, "merge-base", "--is-ancestor", tested_commit, commit)
        git_output(repo, "diff", "--exit-code", tested_commit, commit, "--",
                   "src/rag_cad", "scripts/bootstrap_colab.py")
    if not workspace.is_dir():
        raise ValueError("Working directory must already exist")
    local_path(workspace)
    minimum = profile.get("minimum_free_bytes")
    if type(minimum) is not int or minimum <= 0:
        raise ValueError("Profile must declare a positive free-disk requirement")
    if shutil.disk_usage(workspace).free < minimum:
        raise ValueError("Insufficient temporary disk")
    if sha256(lock) != profile["expected"]["lock_sha256"]:
        raise ValueError("Dependency lock hash mismatch")
    report = {"commit": commit, "dirty": False, "stage": stage, "upstream": upstream,
            "operator": profile.get("operator"),
            "profile_hash": digest(profile)}
    try:
        actual = observed if observed is not None else observe_environment(profile, lock)
        report["environment"] = actual
        validate_profile(profile, stage, actual)
        if observed is None:
            import torch

            if (torch.ones(1, device="cuda") + 1).item() != 2:
                raise ValueError("GPU allocation/operation failed")
        subprocess.run([sys.executable, "-m", "pip", "check"], check=True,
                       capture_output=True, text=True, timeout=120)
    except (ValueError, OSError, RuntimeError, subprocess.SubprocessError) as error:
        message = str(error) if type(error) is ValueError else f"Runtime measurement/check failed: {type(error).__name__}"
        raise PreflightError(message, report) from None
    return report | {"passed": True,
                     "environment_id": digest({"commit": commit, "fingerprint": actual})}