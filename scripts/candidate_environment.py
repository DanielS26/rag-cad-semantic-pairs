"""Record CPU-installed candidate dependencies and conservative storage bounds.

Reads PyPI package metadata only; never imports torch/transformers or fetches model files.
"""

import argparse
import hashlib
import importlib.metadata
import json
import math
import platform
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

GIB = 1024**3
NAMED_MODEL_BYTES = 1162001987
CAD_ARCHIVE_BYTES = 2680084
SEGMENTER_ZIP_BYTES = 4319076


def storage_requirements(installed_bytes: int, wheel_bytes: int) -> dict:
    local_payload = 2 * NAMED_MODEL_BYTES + CAD_ARCHIVE_BYTES + 256 * 1024**2
    smoke_working_reserve = 2 * GIB
    safety = 2 * GIB
    active = math.ceil((local_payload + smoke_working_reserve + safety) / GIB) * GIB
    before_install = max(20 * GIB, math.ceil((active + installed_bytes + 2 * wheel_bytes) / GIB) * GIB)
    return {"named_model_bytes": NAMED_MODEL_BYTES, "model_cache_copies": 2,
            "cad_archive_bytes": CAD_ARCHIVE_BYTES, "segmenter_zip_bytes": SEGMENTER_ZIP_BYTES,
            "segmenter_extracted_reserve_bytes": 256 * 1024**2,
            "installed_dependencies_bytes": installed_bytes, "compressed_wheels_bytes": wheel_bytes,
            "runtime_free_before_install_bytes": before_install,
            "runtime_free_after_install_bytes": active,
            "drive_free_bytes": 128 * 1024**2,
            "drive_basis": "Two smoke runs: 32 MiB each, doubled for partial publication; no Jina weights",
            "scope": "Bounded three-sentence smoke only; runtime capacity measured separately"}


def record(lock: Path, install_report: Path) -> dict:
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        raise ValueError("Candidate lock evidence must be generated on Linux x86-64")
    packages = {}
    paths = set()
    for distribution in importlib.metadata.distributions():
        name = distribution.metadata["Name"].lower().replace("_", "-")
        packages[name] = distribution.version
        for relative in distribution.files or []:
            path = Path(distribution.locate_file(relative))
            if path.is_file():
                paths.add(path.resolve())
    installed_bytes = sum(path.stat().st_size for path in paths)
    downloads = json.loads(install_report.read_text())["install"]
    wheels = []
    for item in downloads:
        name, version = item["metadata"]["name"], item["metadata"]["version"]
        url = f"https://pypi.org/pypi/{name}/{version}/json"
        with urllib.request.urlopen(url, timeout=30) as response:
            metadata = json.load(response)
        filename = urllib.parse.unquote(item["download_info"]["url"].rsplit("/", 1)[-1])
        matches = [entry for entry in metadata["urls"] if entry["filename"] == filename]
        if len(matches) != 1 or not filename.endswith(".whl"):
            raise ValueError("Expected a named PyPI wheel for storage accounting")
        wheels.append({"name": name, "version": version, "file": filename,
                       "bytes": matches[0]["size"], "sha256": matches[0]["digests"]["sha256"]})
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    return {"candidate_only": True, "tested_colab_profile": False, "gpu_used": False,
            "project_commit": commit, "python": platform.python_version(),
            "platform": platform.platform(), "packages": packages, "wheels": wheels,
            "lock_sha256": hashlib.sha256(lock.read_bytes()).hexdigest(),
            "storage": storage_requirements(installed_bytes, sum(item["bytes"] for item in wheels))}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--install-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = record(args.lock, args.install_report)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"lock_sha256": result["lock_sha256"], "storage": result["storage"]}, indent=2))