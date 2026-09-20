"""Small, deterministic provenance primitives without environment secrets."""

import hashlib
import json
import re
import subprocess
from pathlib import Path

CAD_COMMIT = "26e38a67f0a9e1de4cb3a876e4b021900a5d1c27"


def sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def digest(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def reject_secrets(value: object) -> None:
    text = canonical_json(value)
    if re.search(r"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|hf_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,}|-----BEGIN .*PRIVATE KEY-----)", text):
        raise ValueError("Secret-like content is not permitted in artefacts or metadata")


def write_json(path: Path, value: object) -> None:
    reject_secrets(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(canonical_json(value) + "\n")


def git_output(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "--no-optional-locks", "-C", str(repo), *args],
        capture_output=True, text=True, check=False,
    )
    if result.returncode:
        raise ValueError("Git provenance check failed")
    return result.stdout.strip()


def verify_upstream(repo: Path) -> dict:
    git_output(repo, "merge-base", "--is-ancestor", CAD_COMMIT, "HEAD")
    paths = ["src/detector", "src/adversarial_training", "evaluation", "third_party", "requirements.txt", "LICENSE",
             "scripts/rebuild_classifier.sh", "scripts/run_agentdyn_benchmark.sh",
             "scripts/run_agentdojo_benchmark.sh"]
    git_output(repo, "diff", "--exit-code", CAD_COMMIT, "--", *paths)
    return {"cad_commit": CAD_COMMIT, "source_unchanged": True}