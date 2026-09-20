import json
import subprocess
import sys
from pathlib import Path

from rag_cad.cli import main

ROOT = Path(__file__).resolve().parents[1]


def test_cpu_fake_command(tmp_path, capsys):
    assert main(["smoke", "fake", "--output", str(tmp_path / "fake")]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["execution_kind"] == "fake"
    assert report["live_phase1b_passed"] is False


def test_real_commands_refuse_unapproved_profile_before_ml_import(tmp_path):
    arguments = ["environment", "preflight", "--stage", "smoke",
                 "--profile", str(ROOT / "configs/environments/colab_candidate.yaml"),
                 "--lock", "missing.lock", "--commit", "a" * 40,
                 "--workspace", str(tmp_path), "--output", str(tmp_path / "report.json")]
    assert main(arguments) == 2
    assert main(arguments + ["--execute"]) == 2
    assert not (tmp_path / "report.json").exists()


def test_imports_do_not_load_optional_components():
    result = subprocess.run([sys.executable, "-c",
        "import sys; import rag_cad.cli; assert not {'torch','transformers','nltk','faiss','agentdojo'} & set(sys.modules)"],
        cwd=ROOT, env=__import__("os").environ | {"PYTHONPATH": str(ROOT / "src")},
        capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_artefact_cli_roundtrip(tmp_path, capsys):
    import yaml

    source = tmp_path / "source"
    source.mkdir()
    (source / "fixture.txt").write_text("synthetic", encoding="utf-8")
    storage = tmp_path / "storage.yaml"
    storage.write_text(yaml.safe_dump({"artefact_root": str(tmp_path / "store")}), encoding="utf-8")
    metadata = tmp_path / "metadata.json"
    metadata.write_text('{"synthetic": true}', encoding="utf-8")
    assert main(["artefact", "publish", "--source", str(source), "--storage-config", str(storage),
                 "--metadata", str(metadata), "--stage", "smoke", "--run-id", "fixture"]) == 0
    manifest = tmp_path / "store/smoke/fixture/manifest.json"
    assert main(["artefact", "verify", "--manifest", str(manifest)]) == 0
    assert main(["artefact", "restore", "--manifest", str(manifest),
                 "--destination", str(tmp_path / "restored")]) == 0
    assert (tmp_path / "restored/fixture.txt").read_text() == "synthetic"


def test_upstream_cli_routes_only_after_gate(tmp_path, monkeypatch):
    from rag_cad import cli

    calls = []
    arguments = ["upstream", "fetch-cad", "--profile", "missing-profile", "--lock", "missing-lock",
                 "--commit", "a" * 40, "--workspace", str(tmp_path),
                 "--source", str(tmp_path / "upstream"), "--output", str(tmp_path / "result.json")]
    monkeypatch.setattr(cli, "fetch_release", lambda *args, **kwargs: calls.append("fetch"))
    assert main(arguments) == 2
    assert not calls
    monkeypatch.setattr(cli, "_gate", lambda args: ({}, {"synthetic": True}))
    monkeypatch.setattr(cli, "load_config", lambda path: {"synthetic_spec": True})
    monkeypatch.setattr(cli, "validate_release", lambda *args, **kwargs: {"files": []})
    assert main(arguments + ["--execute", "--allow-network"]) == 0
    assert calls == ["fetch"]