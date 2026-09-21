from pathlib import Path
from types import SimpleNamespace

import pytest

from rag_cad.cli import main
from rag_cad.operations.paths import execution_paths, local_path


@pytest.mark.parametrize("path", ["/content/drive/MyDrive/file", "C:/cache/Drive/data",
                                 "\\\\server\\share\\file", "/tmp/drive/../output"])
def test_drive_and_network_paths_fail_before_io(path):
    with pytest.raises(ValueError):
        local_path(Path(path))


@pytest.mark.parametrize("field", ["source", "resources", "model_bundle", "output", "destination"])
def test_each_actual_path_is_guarded(tmp_path, field):
    args = SimpleNamespace(workspace=tmp_path, **{field: Path("/content/drive/MyDrive/forbidden")})
    with pytest.raises(ValueError, match="Drive"):
        execution_paths(args)
    setattr(args, field, tmp_path.parent / "outside")
    with pytest.raises(ValueError, match="inside"):
        execution_paths(args)


def test_output_input_overlap_fails(tmp_path):
    with pytest.raises(ValueError, match="overlap"):
        execution_paths(SimpleNamespace(workspace=tmp_path, source=tmp_path / "input",
                                        output=tmp_path / "input/output"))


def test_linked_parent_is_rejected(tmp_path, monkeypatch):
    original = Path.is_symlink
    linked = tmp_path / "alias"
    monkeypatch.setattr(Path, "is_symlink", lambda path: path == linked or original(path))
    with pytest.raises(ValueError, match="Linked"):
        local_path(linked / "output")


def test_cli_guards_actual_output_before_profile_or_hardware(tmp_path):
    assert main(["environment", "preflight", "--stage", "smoke", "--execute",
                 "--profile", "missing", "--lock", "missing", "--commit", "a" * 40,
                 "--workspace", str(tmp_path), "--output", "/content/drive/MyDrive/out.json"]) == 2


def test_direct_checkpoint_and_resource_reads_guard_paths():
    from rag_cad.cad.upstream_adapter import load_checkpoint
    from rag_cad.operations.upstream import validate_resources

    with pytest.raises(ValueError, match="Drive"):
        load_checkpoint(Path("/content/drive/MyDrive/checkpoint.pt"), "a" * 64)
    with pytest.raises(ValueError, match="Drive"):
        validate_resources({}, Path("/content/drive/MyDrive/resources"))