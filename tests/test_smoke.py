import pytest

from rag_cad.operations.artefacts import publish, restore
from rag_cad.operations.smoke import FakeBackend, smoke_a, smoke_b


def test_fake_smoke_and_restart_contract(tmp_path):
    backend = FakeBackend()
    metadata = {"commit": "f" * 40, "environment_id": "synthetic-only"}
    report = smoke_a(backend, tmp_path / "run-a", metadata, "fake-runtime-a", atol=1e-6, rtol=1e-6)
    assert report["feature_shape"] == [3, 2048]
    assert report["maximum_token_length"] > 0
    assert report["resources_before"]["ram_total_bytes"] > 0
    assert report["resources_after"]["disk_free_bytes"] > 0
    assert report["checkpoint_inspection"]["swap_heads"][0]["parameter_count"] == 557698
    assert report["rag"][1]["checkpoint_id"] != report["rag"][2]["checkpoint_id"]
    assert report["live_phase1b_passed"] is False
    modes = report["representation_modes"]
    assert set(modes["modes"]) == {"repo_compatible", "paper_exact"}
    assert all(entry["shape"] == [3, 2048] and entry["deterministic"] for entry in modes["modes"].values())
    assert modes["isolated_block_identical"] and modes["primary_mode_selected"] is False
    bundle = publish(tmp_path / "run-a", tmp_path / "store", "smoke", "fake-a", metadata)
    restore(bundle / "manifest.json", tmp_path / "restored")
    result = smoke_b(backend, tmp_path / "restored", metadata, "fake-runtime-b")
    assert result["restored_predictions_match"]
    assert result["source_manifest_sha256"] == report["source_manifest_sha256"]
    with pytest.raises(ValueError, match="fresh runtime"):
        smoke_b(backend, tmp_path / "restored", metadata, "fake-runtime-a")
    with pytest.raises(ValueError, match="mismatch"):
        smoke_b(backend, tmp_path / "restored", {}, "fake-runtime-b")


def test_smoke_rejects_nondeterminism(tmp_path):
    class Unstable(FakeBackend):
        calls = 0

        def encode(self, query, sentences):
            self.calls += 1
            return super().encode(query, sentences) + self.calls

    with pytest.raises(AssertionError):
        smoke_a(Unstable(), tmp_path / "bad", {}, "fake", atol=0, rtol=0)


def test_real_backend_forwards_separate_pins_and_offline_permission(tmp_path, monkeypatch):
    import sys
    from types import SimpleNamespace

    from rag_cad.operations import smoke

    profile = {"remote_code_approved": True, "network_approved": False,
               "expected": {"encoder_revision": "a" * 40, "encoder_code_revision": "b" * 40}}
    calls = []

    def encoder(*args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(max_token_length=0)

    monkeypatch.setitem(sys.modules, "nltk", SimpleNamespace(data=SimpleNamespace(path=[])))
    monkeypatch.setattr(smoke, "validate_resources", lambda *args: None)
    monkeypatch.setattr(smoke, "split_units", lambda text: smoke.SENTENCES)
    monkeypatch.setattr(smoke, "JinaEncoder", encoder)
    monkeypatch.setattr(smoke, "load_checkpoint", lambda *args, **kwargs: (object(), {"synthetic": True}))
    backend = smoke.RealBackend(profile, tmp_path, {"files": {"classifier_fullcad.pt": {"sha256": "c" * 64}}},
                                tmp_path, {}, model_bundle=tmp_path / "bundle")
    assert calls == [(("a" * 40, "b" * 40, tmp_path / "bundle"),
                      {"allow_network": False, "allow_remote_code": True, "progress": smoke.mark})]
    assert backend.reference_inspection == {"synthetic": True}
    with pytest.raises(ValueError, match="Network permission"):
        smoke.RealBackend(profile, tmp_path, {}, tmp_path, {}, model_bundle=tmp_path / "bundle",
                          allow_network=True)

def test_progress_steps_are_fixed_vocabulary_and_ordered(tmp_path, monkeypatch):
    import json

    from rag_cad.operations import smoke

    monkeypatch.setattr(smoke, "PROGRESS_PATH", tmp_path / "smoke_progress.json")
    with pytest.raises(ValueError, match="Unknown progress step"):
        smoke.mark("synthetic-secret-step")
    assert not (tmp_path / "smoke_progress.json").exists()
    metadata = {"commit": "f" * 40, "environment_id": "synthetic-only"}
    smoke_a(FakeBackend(), tmp_path / "run-a", metadata, "fake-runtime-a", atol=1e-6, rtol=1e-6)
    steps = json.loads((tmp_path / "smoke_progress.json").read_text(encoding="utf-8"))
    assert steps == ["output_created", "features_encoded", "features_repeated", "determinism_checked",
                     "reference_scored", "modes_compared", "trained_saved", "reload_checked",
                     "retrieval_checked", "rag_swap_checked", "report_written"]
    assert all(step in smoke.STEPS for step in steps)
    monkeypatch.setattr(smoke, "PROGRESS_PATH", tmp_path / "unstable_progress.json")

    class Unstable(FakeBackend):
        calls = 0

        def encode(self, query, sentences):
            self.calls += 1
            return super().encode(query, sentences) + self.calls

    with pytest.raises(AssertionError):
        smoke_a(Unstable(), tmp_path / "bad", {}, "fake", atol=0, rtol=0)
    assert json.loads((tmp_path / "unstable_progress.json").read_text())[-1] == "features_repeated"
    monkeypatch.setattr(smoke, "PROGRESS_PATH", None)
    smoke.mark("report_written")
    assert not (tmp_path / "None").exists()
