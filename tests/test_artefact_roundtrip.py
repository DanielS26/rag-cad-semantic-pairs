import io
import tarfile

import pytest

from rag_cad.operations.artefacts import checked_members, publish, restore, safe_path, verify


def test_publish_restore_integrity_and_immutability(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "sample.json").write_text('{"synthetic":true}', encoding="utf-8")
    published = publish(source, tmp_path / "store", "smoke", "test-run", {"test_only": True})
    manifest = published / "manifest.json"
    assert verify(manifest)["run_id"] == "test-run"
    restore(manifest, tmp_path / "restored")
    assert (tmp_path / "restored/sample.json").read_bytes() == (source / "sample.json").read_bytes()
    with pytest.raises(FileExistsError):
        publish(source, tmp_path / "store", "smoke", "test-run", {})
    with pytest.raises(FileExistsError):
        restore(manifest, tmp_path / "restored")
    (published / "payload.tar.gz").write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="hash"):
        verify(manifest)


def test_incomplete_publication_rejected(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "sample.txt").write_text("synthetic", encoding="utf-8")
    published = publish(source, tmp_path / "store", "smoke", "test-run", {})
    (published / "_SUCCESS").unlink()
    with pytest.raises(ValueError, match="success"):
        verify(published / "manifest.json")


@pytest.mark.parametrize("name", ["../escape", "/absolute", "C:/escape", "a\\b", "NUL", "bad."])
def test_unsafe_paths_fail(name):
    with pytest.raises(ValueError):
        safe_path(name)


def test_archive_link_rejected_without_extraction():
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        member = tarfile.TarInfo("link")
        member.type = tarfile.SYMTYPE
        member.linkname = "outside"
        archive.addfile(member)
    buffer.seek(0)
    with tarfile.open(fileobj=buffer) as archive, pytest.raises(ValueError, match="links"):
        checked_members(archive)