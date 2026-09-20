import pytest

from rag_cad.operations.artefacts import publish, restore
from rag_cad.operations.smoke import FakeBackend, smoke_a, smoke_b


def test_fake_smoke_and_restart_contract(tmp_path):
    backend = FakeBackend()
    metadata = {"commit": "f" * 40, "environment_id": "synthetic-only"}
    report = smoke_a(backend, tmp_path / "run-a", metadata, "fake-runtime-a", atol=1e-6, rtol=1e-6)
    assert report["feature_shape"] == [3, 2048]
    assert report["live_phase1b_passed"] is False
    bundle = publish(tmp_path / "run-a", tmp_path / "store", "smoke", "fake-a", metadata)
    restore(bundle / "manifest.json", tmp_path / "restored")
    result = smoke_b(backend, tmp_path / "restored", metadata, "fake-runtime-b")
    assert result["restored_predictions_match"]
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