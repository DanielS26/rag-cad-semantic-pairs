"""Standalone trusted bootstrap used before the project can be installed.

The notebook verifies this file's SHA-256 against the operator's reviewed value.
No scientific logic or persistent credentials belong in this helper.
"""

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

CAD_COMMIT = "26e38a67f0a9e1de4cb3a876e4b021900a5d1c27"


def validate_request(repo_url: str, commit: str) -> None:
    if not re.fullmatch(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.git", repo_url):
        raise ValueError("Expected a clean GitHub HTTPS repository URL")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("An exact reviewed commit is required")


def _run(command: list[str], *, cwd=None, env=None) -> str:
    result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError("Bootstrap subprocess failed; credentials and raw output suppressed")
    return result.stdout.strip()


def verify_checkout(checkout: Path, repo_url: str, commit: str) -> None:
    validate_request(repo_url, commit)
    if _run(["git", "rev-parse", "HEAD"], cwd=checkout) != commit:
        raise ValueError("Exact commit verification failed")
    if _run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=checkout):
        raise ValueError("Bootstrap checkout is dirty")
    if _run(["git", "remote", "get-url", "origin"], cwd=checkout) != repo_url:
        raise ValueError("Remote URL verification failed")
    _run(["git", "merge-base", "--is-ancestor", CAD_COMMIT, "HEAD"], cwd=checkout)


def clone_exact(repo_url: str, commit: str, checkout: Path, token: str | None = None) -> None:
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
                  repo_url, str(checkout)], env=environment)
    finally:
        environment.pop("GH_READ_TOKEN", None)
        environment.pop("GIT_ASKPASS", None)
        token = None
    _run(["git", "checkout", "--detach", commit], cwd=checkout)
    verify_checkout(checkout, repo_url, commit)


def install_and_test(checkout: Path, repo_url: str, commit: str, lock_relative: str) -> None:
    verify_checkout(checkout, repo_url, commit)
    lock = (checkout / lock_relative).resolve()
    if not lock.is_relative_to(checkout.resolve()) or not lock.name.endswith(".lock.txt") or not lock.is_file():
        raise ValueError("A reviewed committed dependency lock is required")
    _run([sys.executable, "-m", "pip", "install", "-r", str(lock)], cwd=checkout)
    _run([sys.executable, "-m", "pip", "install", "-e", ".", "--no-deps", "--no-build-isolation"], cwd=checkout)
    _run([sys.executable, "-m", "pip", "check"], cwd=checkout)
    _run([sys.executable, "-m", "pytest", "-m", "not gpu and not integration", "-q"], cwd=checkout)
    verify_checkout(checkout, repo_url, commit)