import hashlib
import io
import json
import subprocess
import tarfile
from pathlib import Path

import pytest

from rag_cad.config import load_config
from rag_cad.data.cad_release_adapter import validate_archive
from rag_cad.operations.provenance import CAD_COMMIT, verify_upstream
from rag_cad.operations.upstream import fetch_release, validate_release_spec

ROOT = Path(__file__).resolve().parents[1]


def test_upstream_ancestry_and_preservation():
    assert verify_upstream(ROOT)["source_unchanged"]
    subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", CAD_COMMIT, "HEAD"], check=True)


def test_project_python_source_is_not_hidden_by_inherited_ignore_rules():
    for path in (ROOT / "src/rag_cad").rglob("*.py"):
        relative = path.relative_to(ROOT).as_posix()
        result = subprocess.run(["git", "-C", str(ROOT), "check-ignore", "--no-index", relative],
                                capture_output=True, text=True)
        assert result.returncode == 1, f"Project source is ignored: {relative}"


def test_named_release_manifest_and_explicit_network_gate(tmp_path):
    spec = load_config(ROOT / "configs/upstream/cad_release.yaml")
    validate_release_spec(spec)
    with pytest.raises(ValueError, match="authorisation"):
        fetch_release(spec, tmp_path / "upstream")


def test_fetch_transport_uses_exact_revisions_and_hashes(tmp_path):
    spec = load_config(ROOT / "configs/upstream/cad_release.yaml")
    payload = b"synthetic fixture, not official data"
    urls = []
    for entry in spec["files"].values():
        entry.update(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())

    def opener(url, timeout):
        urls.append(url)
        return io.BytesIO(payload)

    assert len(fetch_release(spec, tmp_path, allow_network=True, opener=opener)) == 4
    assert all("/resolve/" in url and "/main/" not in url for url in urls)
    (tmp_path / "classifier_fullcad.pt").write_bytes(b"wrong")
    with pytest.raises(ValueError, match="integrity"):
        fetch_release(spec, tmp_path, allow_network=True, opener=opener)


def test_archive_counts_and_hash_validation(tmp_path):
    record = {"user": "synthetic", "sentence_segments": "[0] First.\n[1] Target.",
              "injection_span_unit": {"start": 1, "end": 1}}
    payload = json.dumps(record).encode()
    path = tmp_path / "fixture.tar.gz"
    with tarfile.open(path, "w:gz") as archive:
        member = tarfile.TarInfo("fixture.json")
        member.size = len(payload)
        archive.addfile(member, io.BytesIO(payload))
    spec = {"kind": "original_train", "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "counts": {"records": 1, "rows": 2, "malicious": 1, "benign": 1, "count_mismatches": 0}}
    assert validate_archive(path, spec)["counts"]["rows"] == 2
    spec["counts"]["rows"] = 3
    with pytest.raises(ValueError, match="counts"):
        validate_archive(path, spec)


def test_pinned_segmenter_resource_and_extracted_integrity(tmp_path):
    import zipfile

    from rag_cad.operations.provenance import digest
    from rag_cad.operations.upstream import prepare_resources, validate_resources

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("punkt_tab/english/synthetic.txt", "synthetic fixture")
    payload = buffer.getvalue()
    resource = {"revision": "a" * 40, "sha256": hashlib.sha256(payload).hexdigest()}
    profile = {"segmenter_resource": resource, "expected": {"segmenter": digest(resource)}}
    destination = tmp_path / "resources"
    prepare_resources(profile, destination, allow_network=True,
                      opener=lambda url, timeout: io.BytesIO(payload))
    validate_resources(profile, destination)
    (destination / "tokenizers/punkt_tab/english/synthetic.txt").write_text("tampered")
    with pytest.raises(ValueError, match="changed"):
        validate_resources(profile, destination)