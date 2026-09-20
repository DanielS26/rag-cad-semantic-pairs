"""Immutable local-filesystem protocol, also usable on a mounted artefact store."""

import json
import re
import shutil
import tarfile
from pathlib import Path, PurePosixPath, PureWindowsPath

from rag_cad.operations.provenance import reject_secrets, sha256, write_json


def safe_path(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if (
        not name or "\\" in name or ":" in name or path.is_absolute()
        or PureWindowsPath(name).drive or ".." in path.parts or path == PurePosixPath(".")
        or any(part.endswith((".", " ")) for part in path.parts)
        or any(re.fullmatch(r"(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", part)
               for part in path.parts)
    ):
        raise ValueError("Unsafe relative path")
    return path


def checked_members(archive: tarfile.TarFile) -> list[tarfile.TarInfo]:
    members = archive.getmembers()
    if len(members) > 10000 or sum(member.size for member in members) > 1024**3:
        raise ValueError("Archive exceeds bounded extraction limits")
    seen = set()
    for member in members:
        path = safe_path(member.name)
        key = str(path).casefold()
        if key in seen or not (member.isfile() or member.isdir()):
            raise ValueError("Archive contains duplicate paths, links, or special members")
        seen.add(key)
    return members


def _inventory(source: Path) -> list[dict]:
    files = []
    if not source.is_dir() or source.is_symlink():
        raise ValueError("Source must be a regular directory")
    for path in sorted(source.rglob("*")):
        if path.is_symlink():
            raise ValueError("Symbolic links are forbidden")
        if path.is_file():
            relative = path.relative_to(source).as_posix()
            safe_path(relative)
            if path.suffix in {".json", ".jsonl", ".yaml", ".txt", ".log", ".md"}:
                reject_secrets(path.read_text(encoding="utf-8"))
            if path.name == ".env" or path.name.endswith((".pem", ".key")):
                raise ValueError("Credential files are forbidden")
            files.append({"path": relative, "size": path.stat().st_size, "sha256": sha256(path)})
    if not files:
        raise ValueError("Empty artefact source")
    return files


def publish(source: Path, root: Path, stage: str, run_id: str, metadata: dict) -> Path:
    for value in (stage, run_id):
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", value):
            raise ValueError("Invalid stage or run ID")
    reject_secrets(metadata)
    files = _inventory(source)
    destination = root / stage / run_id
    partial = destination.with_name(run_id + ".partial")
    if destination.exists() or partial.exists():
        raise FileExistsError("Run IDs are immutable, including incomplete publications")
    if root.resolve().is_relative_to(source.resolve()):
        raise ValueError("Artefact store must not be inside its source")
    partial.mkdir(parents=True)
    payload = partial / "payload.tar.gz"
    with tarfile.open(payload, "w:gz") as archive:
        for item in files:
            archive.add(source / item["path"], arcname=item["path"], recursive=False)
    manifest = {"format_version": 1, "stage": stage, "run_id": run_id, "metadata": metadata,
                "files": files, "payload_sha256": sha256(payload)}
    write_json(partial / "manifest.json", manifest)
    checksums = f"{manifest['payload_sha256']}  payload.tar.gz\n{sha256(partial / 'manifest.json')}  manifest.json\n"
    (partial / "SHA256SUMS").write_text(checksums, encoding="ascii")
    _verify(partial, complete=False)
    partial.rename(destination)
    _verify(destination, complete=False)
    (destination / "_SUCCESS").write_text(sha256(destination / "manifest.json"), encoding="ascii")
    verify(destination / "manifest.json")
    return destination


def _verify(directory: Path, complete: bool) -> dict:
    manifest_path = directory / "manifest.json"
    for filename in ("manifest.json", "payload.tar.gz", "SHA256SUMS"):
        if (directory / filename).is_symlink():
            raise ValueError("Artefact metadata/payload links are forbidden")
    if complete and (
        not (directory / "_SUCCESS").is_file()
        or (directory / "_SUCCESS").is_symlink()
        or (directory / "_SUCCESS").read_text(encoding="ascii") != sha256(manifest_path)
    ):
        raise ValueError("Missing or invalid success marker")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("format_version") != 1:
        raise ValueError("Unknown artefact version")
    payload = directory / "payload.tar.gz"
    if sha256(payload) != manifest["payload_sha256"]:
        raise ValueError("Payload hash mismatch")
    expected_checksums = f"{manifest['payload_sha256']}  payload.tar.gz\n{sha256(manifest_path)}  manifest.json\n"
    if (directory / "SHA256SUMS").read_text(encoding="ascii") != expected_checksums:
        raise ValueError("Checksum manifest mismatch")
    expected = {item["path"]: item for item in manifest["files"]}
    if len(expected) != len(manifest["files"]):
        raise ValueError("Duplicate manifest paths")
    for name in expected:
        safe_path(name)
    with tarfile.open(payload, "r:gz") as archive:
        members = checked_members(archive)
        if {member.name for member in members} != set(expected):
            raise ValueError("Payload and manifest paths differ")
        import hashlib

        for member in members:
            if not member.isfile() or member.size != expected[member.name]["size"]:
                raise ValueError("Payload file type or size mismatch")
            with archive.extractfile(member) as handle:
                actual = hashlib.file_digest(handle, "sha256").hexdigest()
            if actual != expected[member.name]["sha256"]:
                raise ValueError("Payload member hash mismatch")
    return manifest


def verify(manifest: Path) -> dict:
    if manifest.name != "manifest.json":
        raise ValueError("Expected an artefact manifest.json")
    return _verify(manifest.parent, complete=True)


def restore(manifest: Path, destination: Path) -> dict:
    result = verify(manifest)
    if destination.exists():
        raise FileExistsError("Restore destination must be new")
    destination.mkdir(parents=True)
    with tarfile.open(manifest.parent / "payload.tar.gz", "r:gz") as archive:
        for member in checked_members(archive):
            target = destination.joinpath(*safe_path(member.name).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.extractfile(member) as source, target.open("xb") as output:
                shutil.copyfileobj(source, output)
    if _inventory(destination) != result["files"]:
        raise ValueError("Restored files failed integrity verification")
    return result