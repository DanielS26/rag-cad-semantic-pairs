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
                 "--destination", str(tmp_path / "restored"),
                 "--receipt", str(tmp_path / "receipt.json")]) == 0
    assert (tmp_path / "restored/fixture.txt").read_text() == "synthetic"
    from rag_cad.operations.artefacts import verify_restored

    assert verify_restored(tmp_path / "receipt.json", tmp_path / "restored")["manifest"]["run_id"] == "fixture"
    (tmp_path / "restored/fixture.txt").write_text("changed", encoding="utf-8")
    import pytest

    with pytest.raises(ValueError, match="changed"):
        verify_restored(tmp_path / "receipt.json", tmp_path / "restored")


def test_failed_discovery_report_written_before_cli_refuses(tmp_path, monkeypatch):
    from rag_cad import cli
    from rag_cad.operations.preflight import PreflightError

    def fail(args):
        raise PreflightError("Measured GPU memory must exceed 8 GiB", {"environment": {"gpu_memory_bytes": 0}})

    monkeypatch.setattr(cli, "_gate", fail)
    output = tmp_path / "failed.json"
    assert main(["environment", "preflight", "--profile", "synthetic", "--lock", "synthetic",
                 "--stage", "smoke", "--commit", "a" * 40, "--workspace", str(tmp_path),
                 "--output", str(output)]) == 2
    assert json.loads(output.read_text())["passed"] is False


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


def test_real_smoke_cli_preserves_validation_and_publication_evidence(tmp_path, monkeypatch):
    from rag_cad import cli
    from rag_cad.operations.smoke import FakeBackend

    captured = {}
    source = tmp_path / "inputs"
    source.mkdir()
    profile = {"tolerance": {"atol": 1e-6, "rtol": 1e-5}}
    evidence = {"commit": "a" * 40, "synthetic_test": True}
    release = {"files": [{"file": "fixture.pt", "checkpoint_inspection": {"parameter_count": 557698}}]}

    def backend(*args, **kwargs):
        captured.update(kwargs)
        return FakeBackend()

    monkeypatch.setattr(cli, "_gate", lambda args: (profile, evidence))
    monkeypatch.setattr(cli, "validate_release", lambda *args, **kwargs: release)
    monkeypatch.setattr(cli, "RealBackend", backend)
    arguments = ["smoke", "run-a", "--profile", "synthetic", "--lock", "synthetic",
                 "--release", str(ROOT / "configs/upstream/cad_release.yaml"), "--commit", "a" * 40,
                 "--workspace", str(tmp_path), "--source", str(source), "--resources", str(source),
                 "--model-bundle", str(tmp_path / "model"), "--output", str(tmp_path / "run-a"), "--execute"]
    assert main(arguments) == 0
    assert captured["allow_network"] is False
    assert captured["model_bundle"] == tmp_path / "model"
    assert json.loads((tmp_path / "run-a/source_manifest.json").read_text()) == release
    report = json.loads((tmp_path / "run-a/run_a.json").read_text())
    assert report["metadata"] == evidence
    assert report["source_manifest_sha256"]
    assert report["timings_seconds"]["release_validation"] >= 0


def test_profile_and_flag_both_required_for_downloads(tmp_path, monkeypatch):
    from rag_cad import cli

    monkeypatch.setattr(cli, "load_config", lambda path: {"network_approved": False, "compute_budget_approved": True})
    arguments = ["upstream", "fetch-cad", "--profile", "synthetic", "--lock", "synthetic",
                 "--commit", "a" * 40, "--workspace", str(tmp_path), "--source", str(tmp_path / "source"),
                 "--output", str(tmp_path / "audit.json"), "--execute", "--allow-network"]
    assert main(arguments) == 2
    assert not (tmp_path / "source").exists()


def test_compute_budget_is_not_implicitly_approved(tmp_path, monkeypatch):
    from rag_cad import cli

    monkeypatch.setattr(cli, "load_config", lambda path: {"approved": True, "compute_budget_approved": False})

    def forbidden(*args, **kwargs):
        raise AssertionError("Must not inspect GPU before budget approval")

    monkeypatch.setattr(cli, "preflight", forbidden)
    assert main(["environment", "preflight", "--stage", "smoke", "--execute",
                 "--profile", "synthetic", "--lock", "synthetic", "--commit", "a" * 40,
                 "--workspace", str(tmp_path), "--output", str(tmp_path / "report.json")]) == 2