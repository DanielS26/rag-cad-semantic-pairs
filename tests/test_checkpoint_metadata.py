import numpy as np
import pytest

from rag_cad.cad.upstream_adapter import STATE_SHAPES, load_checkpoint, validate_checkpoint


def test_synthetic_checkpoint_metadata_and_shapes():
    checkpoint = {"input_dim": 2048, "d_hid": 256, "dropout": 0.3, "best_threshold": 0.5,
                  "model_state_dict": {name: np.zeros(shape, dtype=np.float32)
                                       for name, shape in STATE_SHAPES.items()}}
    validate_checkpoint(checkpoint)
    with pytest.raises(ValueError, match="metadata"):
        validate_checkpoint(checkpoint | {"input_dim": 1024})
    checkpoint["model_state_dict"]["net.6.bias"][0] = np.nan
    with pytest.raises(ValueError, match="finite"):
        validate_checkpoint(checkpoint)


def test_hash_failure_precedes_torch_import(tmp_path):
    path = tmp_path / "synthetic.pt"
    path.write_bytes(b"not a pickle")
    with pytest.raises(ValueError, match="before deserialization"):
        load_checkpoint(path, "0" * 64)


def test_checkpoint_loader_uses_weights_only_and_strict_state(tmp_path, monkeypatch):
    import sys
    from types import SimpleNamespace

    from rag_cad.cad import upstream_adapter
    from rag_cad.operations.provenance import sha256

    checkpoint = {"input_dim": 2048, "d_hid": 256, "dropout": 0.3, "best_threshold": 0.5,
                  "model_state_dict": {name: np.zeros(shape, dtype=np.float32)
                                       for name, shape in STATE_SHAPES.items()}}
    calls = []

    def load(path, **kwargs):
        calls.append(kwargs)
        return checkpoint

    class FakeHead:
        def load_state_dict(self, state, strict):
            assert strict is True and state is checkpoint["model_state_dict"]

        def eval(self):
            return self

    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(load=load))
    monkeypatch.setattr(upstream_adapter, "classifier", FakeHead)
    path = tmp_path / "fixture.pt"
    path.write_bytes(b"synthetic, loader mocked")
    assert isinstance(load_checkpoint(path, sha256(path)), FakeHead)
    assert calls == [{"map_location": "cpu", "weights_only": True}]