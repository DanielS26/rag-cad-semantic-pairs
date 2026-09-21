"""Named release acquisition; no download occurs at import time."""

import hashlib
import shutil
import urllib.request
from pathlib import Path

from rag_cad.cad.upstream_adapter import load_checkpoint
from rag_cad.config import require_sha
from rag_cad.data.cad_release_adapter import validate_archive
from rag_cad.operations.paths import local_path
from rag_cad.operations.provenance import CAD_COMMIT, sha256

NAMED_FILES = {"training_data_original.tar.gz", "testing_data_original.tar.gz",
               "training_data_paraphrased.tar.gz", "classifier_fullcad.pt"}


def validate_release_spec(spec: dict) -> None:
    if spec.get("cad_commit") != CAD_COMMIT or set(spec.get("files", {})) != NAMED_FILES:
        raise ValueError("Unapproved upstream commit or release filenames")
    if spec.get("data_repository") != "tavialiu/CAD-data" or spec.get("models_repository") != "tavialiu/CAD-models":
        raise ValueError("Unknown upstream repository")
    for key in ("data_revision", "models_revision"):
        require_sha(spec.get(key))
    for filename, entry in spec["files"].items():
        require_sha(entry.get("sha256"), 64)
        if entry.get("repository_type") not in {"model", "dataset"}:
            raise ValueError("Unknown release repository type")
        if type(entry.get("bytes")) is not int or entry["bytes"] <= 0:
            raise ValueError("Release size must be positive")
        if filename.endswith(".pt") != (entry.get("repository_type") == "model"):
            raise ValueError("Release repository type mismatch")


def fetch_release(spec: dict, destination: Path, *, allow_network: bool = False,
                  opener=urllib.request.urlopen) -> list[str]:
    validate_release_spec(spec)
    local_path(destination)
    if allow_network is not True:
        raise ValueError("Explicit network authorisation is required")
    destination.mkdir(parents=True, exist_ok=True)
    fetched = []
    for filename, entry in spec["files"].items():
        target = destination / filename
        local_path(target)
        if target.exists():
            if target.stat().st_size != entry["bytes"] or sha256(target) != entry["sha256"]:
                raise ValueError("Existing release file failed integrity check")
            fetched.append(filename)
            continue
        is_model = entry["repository_type"] == "model"
        repository = spec["models_repository" if is_model else "data_repository"]
        revision = spec["models_revision" if is_model else "data_revision"]
        prefix = "" if is_model else "datasets/"
        url = f"https://huggingface.co/{prefix}{repository}/resolve/{revision}/{filename}"
        partial = target.with_name(filename + ".partial")
        with partial.open("xb") as output, opener(url, timeout=60) as response:
            remaining = entry["bytes"]
            while remaining:
                chunk = response.read(min(1024 * 1024, remaining))
                if not chunk:
                    raise ValueError("Incomplete upstream download")
                output.write(chunk)
                remaining -= len(chunk)
            if response.read(1):
                raise ValueError("Upstream download exceeds declared size")
        if sha256(partial) != entry["sha256"]:
            raise ValueError("Upstream download hash mismatch")
        partial.rename(target)
        fetched.append(filename)
    return fetched


def validate_release(spec: dict, source: Path, *, load_model: bool = False) -> dict:
    local_path(source)
    validate_release_spec(spec)
    results = []
    for filename, entry in spec["files"].items():
        path = source / filename
        local_path(path)
        if path.stat().st_size != entry["bytes"] or sha256(path) != entry["sha256"]:
            raise ValueError("Release hash/size mismatch")
        if entry["kind"] == "checkpoint":
            inspection = None
            if load_model:
                _, inspection = load_checkpoint(path, entry["sha256"], with_inspection=True)
            results.append({"file": filename, "bytes": path.stat().st_size,
                            "sha256": sha256(path), "safely_loaded": load_model,
                            "checkpoint_inspection": inspection})
        else:
            results.append(validate_archive(path, entry))
    return {"cad_commit": spec["cad_commit"], "data_revision": spec["data_revision"],
            "models_revision": spec["models_revision"], "files": results}


def prepare_resources(profile: dict, destination: Path, *, allow_network: bool = False,
                      opener=urllib.request.urlopen) -> None:
    import zipfile

    from rag_cad.operations.artefacts import safe_path

    resource = profile.get("segmenter_resource", {})
    local_path(destination)
    revision = require_sha(resource.get("revision"))
    expected_hash = require_sha(resource.get("sha256"), 64)
    if allow_network is not True:
        raise ValueError("Explicit resource-download authorisation is required")
    if destination.exists():
        raise FileExistsError("Resource destination must be new")
    destination.mkdir(parents=True)
    archive_path = destination / "punkt_tab.zip"
    local_path(archive_path)
    url = f"https://raw.githubusercontent.com/nltk/nltk_data/{revision}/packages/tokenizers/punkt_tab.zip"
    with archive_path.open("xb") as output, opener(url, timeout=60) as response:
        total = 0
        while chunk := response.read(1024 * 1024):
            total += len(chunk)
            if total > 64 * 1024**2:
                raise ValueError("Compressed segmenter resource is too large")
            output.write(chunk)
    if sha256(archive_path) != expected_hash:
        raise ValueError("Segmenter resource hash mismatch")
    with zipfile.ZipFile(archive_path) as archive:
        members = archive.infolist()
        if sum(member.file_size for member in members) > 256 * 1024**2:
            raise ValueError("Segmenter resource is too large")
        seen = set()
        for member in members:
            path = safe_path(member.filename.rstrip("/"))
            if str(path).casefold() in seen or (member.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("Resource contains duplicate paths or symbolic links")
            seen.add(str(path).casefold())
        for member in members:
            target = destination / "tokenizers" / member.filename
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as source, target.open("xb") as output:
                    shutil.copyfileobj(source, output)
    validate_resources(profile, destination)


def validate_resources(profile: dict, destination: Path) -> None:
    local_path(destination)
    import zipfile

    from rag_cad.operations.artefacts import safe_path
    from rag_cad.operations.provenance import digest

    resource = profile["segmenter_resource"]
    local_path(destination / "punkt_tab.zip")
    if digest(resource) != profile["expected"]["segmenter"]:
        raise ValueError("Segmenter fingerprint mismatch")
    if sha256(destination / "punkt_tab.zip") != resource["sha256"]:
        raise ValueError("Segmenter resource hash mismatch")
    with zipfile.ZipFile(destination / "punkt_tab.zip") as archive:
        expected_files = set()
        for member in archive.infolist():
            relative = safe_path(member.filename.rstrip("/"))
            if member.is_dir():
                continue
            expected_files.add(str(relative))
            target = destination / "tokenizers" / str(relative)
            local_path(target)
            if target.is_symlink() or not target.is_file():
                raise ValueError("Segmenter resource file missing or linked")
            with archive.open(member) as source:
                expected_hash = hashlib.file_digest(source, "sha256").hexdigest()
            if sha256(target) != expected_hash:
                raise ValueError("Extracted segmenter resource changed")
        actual_files = {path.relative_to(destination / "tokenizers").as_posix()
                        for path in (destination / "tokenizers").rglob("*") if path.is_file()}
        if actual_files != expected_files:
            raise ValueError("Unexpected segmenter resource files")