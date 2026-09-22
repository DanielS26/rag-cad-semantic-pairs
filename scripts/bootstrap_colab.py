"""Standalone trusted bootstrap used before the project can be installed.

The notebook verifies this file's SHA-256 against the operator's reviewed value.
No scientific logic or persistent credentials belong in this helper.
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CAD_COMMIT = "26e38a67f0a9e1de4cb3a876e4b021900a5d1c27"
STAGES = frozenset({
    "git_clone", "git_checkout", "checkout_verification", "virtual_environment_create",
    "locked_dependency_install", "editable_project_install", "pip_check", "cpu_tests",
    "environment_preflight", "artefact_restore", "upstream_fetch",
    "smoke_run_a", "smoke_run_b", "conformance_released_test", "artefact_publish",
})


def validate_request(repo_url: str, commit: str) -> None:
    if not re.fullmatch(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.git", repo_url):
        raise ValueError("Expected a clean GitHub HTTPS repository URL")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("An exact reviewed commit is required")


def _run(command: list[str], *, stage="checkout_verification", cwd=None, env=None, timeout=120) -> str:
    if stage not in STAGES:
        raise ValueError("Invalid subprocess stage")
    failure = None
    try:
        result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, check=False, timeout=timeout)
        if result.returncode:
            failure = f"exit_code={result.returncode}" if type(result.returncode) is int else "failed"
    except subprocess.TimeoutExpired:
        failure = "timed_out"
    except subprocess.CalledProcessError as error:
        failure = f"exit_code={error.returncode}" if type(error.returncode) is int else "failed"
    except Exception:
        failure = "failed"
    if failure is not None:
        raise RuntimeError(f"{stage}: {failure}") from None
    return result.stdout.strip()


def run_stage(command: list[str], *, stage: str, cwd=None, timeout=120) -> None:
    output = _run(command, stage=stage, cwd=cwd, timeout=timeout)
    if output:
        print(output)


def verify_checkout(checkout: Path, repo_url: str, commit: str) -> None:
    validate_request(repo_url, commit)
    if _run(["git", "rev-parse", "HEAD"], cwd=checkout) != commit:
        raise ValueError("Exact commit verification failed")
    if _run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=checkout):
        raise ValueError("Bootstrap checkout is dirty")
    if _run(["git", "remote", "get-url", "origin"], cwd=checkout) != repo_url:
        raise ValueError("Remote URL verification failed")
    _run(["git", "merge-base", "--is-ancestor", CAD_COMMIT, "HEAD"], cwd=checkout)


def clone_exact(repo_url: str, commit: str, checkout: Path, token: str | None = None, *,
                allow_network: bool = False) -> None:
    if allow_network is not True:
        raise ValueError("Explicit network permission is required for Git checkout")
    validate_request(repo_url, commit)
    if checkout.exists():
        raise FileExistsError("Bootstrap requires a fresh checkout destination")
    environment = os.environ.copy()
    for name in ("GH_TOKEN", "GITHUB_TOKEN", "GH_READ_TOKEN"):
        environment.pop(name, None)
    environment["GIT_TERMINAL_PROMPT"] = "0"
    try:
        with tempfile.TemporaryDirectory(prefix="rag-cad-askpass-") as temporary:
            askpass = Path(temporary) / "askpass.sh"
            askpass.write_text(
                '#!/bin/sh\ncase "$1" in\n'
                '  *Username*) printf "%s\\n" "x-access-token" ;;\n'
                '  *Password*) printf "%s\\n" "$GH_READ_TOKEN" ;;\n'
                '  *) exit 1 ;;\nesac\n', encoding="utf-8",
            )
            askpass.chmod(0o700)
            environment["GIT_ASKPASS"] = str(askpass)
            if token:
                environment["GH_READ_TOKEN"] = token
            _run(["git", "-c", "credential.helper=", "clone", "--no-checkout",
                repo_url, str(checkout)], stage="git_clone", env=environment)
    finally:
        environment.pop("GH_READ_TOKEN", None)
        environment.pop("GIT_ASKPASS", None)
        token = None
    _run(["git", "checkout", "--detach", commit], stage="git_checkout", cwd=checkout)
    verify_checkout(checkout, repo_url, commit)


def environment_python(environment: Path) -> Path:
    """Interpreter of the isolated project environment created by install_and_test."""
    return environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def install_and_test(checkout: Path, repo_url: str, commit: str, lock_relative: str, *,
                     allow_network: bool = False, timeout: float = 3600,
                     environment: Path | None = None) -> Path:
    """Install the committed lock into a fresh isolated environment and return its interpreter.

    Colab's system interpreter carries hundreds of preinstalled packages whose declared
    requirements conflict with each other and with the candidate lock, so dependency
    checks and project commands run only inside the isolated environment. Colab's Python
    build lacks ensurepip, so the environment is created without pip and the system pip
    installs the lock (which pins pip and setuptools) into it via ``--python``.
    """
    if allow_network is not True:
        raise ValueError("Explicit network permission is required for dependency installation")
    verify_checkout(checkout, repo_url, commit)
    lock = (checkout / lock_relative).resolve()
    if not lock.is_relative_to(checkout.resolve()) or not lock.name.endswith(".lock.txt") or not lock.is_file():
        raise ValueError("A reviewed committed dependency lock is required")
    environment = (checkout.parent / "rag-cad-venv" if environment is None else Path(environment)).resolve()
    if environment.is_relative_to(checkout.resolve()) or environment.exists():
        raise ValueError("A fresh isolated environment outside the checkout is required")
    evidence = json.loads((checkout / "configs/environments/colab_candidate_cpu_evidence.json").read_text(encoding="utf-8"))
    if hashlib.sha256(lock.read_bytes()).hexdigest() != evidence["lock_sha256"]:
        raise ValueError("Candidate lock differs from Ubuntu CPU evidence")
    if shutil.disk_usage(checkout).free < evidence["storage"]["runtime_free_before_install_bytes"]:
        raise ValueError("Insufficient disk for locked installation and smoke working space")
    python = str(environment_python(environment))
    deadline = time.monotonic() + min(timeout, 10800)
    commands = [
        ("virtual_environment_create", [sys.executable, "-m", "venv", "--without-pip", str(environment)]),
        ("locked_dependency_install", [sys.executable, "-m", "pip", "--python", python, "install",
                                       "--no-cache-dir", "-r", str(lock)]),
        ("editable_project_install", [python, "-m", "pip", "install", "-e", ".", "--no-deps", "--no-build-isolation"]),
        ("pip_check", [python, "-m", "pip", "check"]),
        ("cpu_tests", [python, "-m", "pytest", "-m", "not gpu and not integration", "-q"]),
    ]
    for stage, command in commands:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ValueError("Installation/test budget exhausted; disconnect runtime")
        _run(command, stage=stage, cwd=checkout, timeout=remaining)
    verify_checkout(checkout, repo_url, commit)
    return environment_python(environment)


def remaining_seconds(started: float, connected_seconds_used: float,
                      units_used: float, units_per_hour: float) -> float:
    import math

    values = (started, connected_seconds_used, units_used, units_per_hour)
    if any(type(value) not in (float, int) or not math.isfinite(value) or value < 0 for value in values):
        raise ValueError("Budget observations must be finite nonnegative numbers")
    if units_per_hour <= 0:
        raise ValueError("Enter Colab's displayed compute-unit rate")
    elapsed = max(0.0, time.monotonic() - started)
    remaining = min(10800 - connected_seconds_used, (20 - units_used) * 3600 / units_per_hour) - elapsed
    if remaining <= 0:
        raise ValueError("Combined Run A/B budget exhausted; disconnect and delete runtime")
    return remaining
