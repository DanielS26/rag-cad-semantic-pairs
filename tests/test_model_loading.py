import json
import socket
import sys
from types import SimpleNamespace

import pytest

from rag_cad.cad import representation
from rag_cad.cad.model_bundle import (
    CODE_FILES,
    CODE_REPO,
    MODEL_FILES,
    MODEL_REPO,
    offline_execution,
    prepare_bundle,
)

WEIGHTS = "a" * 40
CODE = "b" * 40


def fake_downloads(tmp_path):
    calls = []
    cache = tmp_path / "synthetic-cache"
    cache.mkdir()

    def download(**kwargs):
        calls.append(kwargs)
        path = cache / kwargs["filename"]
        if path.name == "config.json":
            path.write_text(json.dumps({"auto_map": {"AutoModel": CODE_REPO + "--modeling_lora.XLMRobertaLoRA"}}))
        elif path.name.endswith(".json"):
            path.write_text("{}")
        else:
            path.write_bytes(b"synthetic fixture; never executed")
        return path

    return calls, download


def test_separate_repositories_revisions_and_verified_offline_reuse(tmp_path):
    calls, download = fake_downloads(tmp_path)
    root = tmp_path / "bundle"
    manifest = prepare_bundle(root, WEIGHTS, CODE, allow_network=True, download=download)
    assert manifest["weights_revision"] == WEIGHTS and manifest["code_revision"] == CODE
    assert {(call["repo_id"], call["revision"]) for call in calls} == {(MODEL_REPO, WEIGHTS), (CODE_REPO, CODE)}
    assert len(calls) == len(MODEL_FILES + CODE_FILES)
    assert all(call["token"] is False for call in calls)
    assert "--" not in (root / "config.json").read_text()
    assert prepare_bundle(root, WEIGHTS, CODE) == manifest
    with pytest.raises(ValueError, match="revisions"):
        prepare_bundle(root, WEIGHTS, "c" * 40)
    (root / "model.safetensors").write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="integrity"):
        prepare_bundle(root, WEIGHTS, CODE)


def test_default_denial_precedes_any_optional_import_or_download(tmp_path):
    with pytest.raises(ValueError, match="remote-code permission"):
        representation.JinaEncoder(WEIGHTS, CODE, tmp_path / "missing")
    with pytest.raises(ValueError, match="network permission"):
        representation.JinaEncoder(WEIGHTS, CODE, tmp_path / "missing", allow_remote_code=True)
    with pytest.raises(ValueError, match="hash"):
        prepare_bundle(tmp_path / "missing", "main", CODE, allow_network=True)


def test_loaders_are_local_and_execution_denies_network(tmp_path, monkeypatch):
    calls, download = fake_downloads(tmp_path)
    bundle = tmp_path / "bundle"
    prepare_bundle(bundle, WEIGHTS, CODE, allow_network=True, download=download)
    loads = []

    class Auto:
        @classmethod
        def from_pretrained(cls, path, **kwargs):
            loads.append((path, kwargs))
            assert kwargs["local_files_only"] is True
            with pytest.raises(RuntimeError, match="Network"):
                socket.create_connection(("example.invalid", 443))
            return cls()

        def to(self, device):
            return self

        def eval(self):
            return self

    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(float32="float32"))
    monkeypatch.setitem(sys.modules, "transformers", SimpleNamespace(AutoModel=Auto, AutoTokenizer=Auto))
    representation.JinaEncoder(WEIGHTS, CODE, bundle, allow_remote_code=True)
    assert all(path == str(bundle.resolve()) for path, _ in loads)
    assert loads[1][1]["use_flash_attn"] is False
    with offline_execution(), pytest.raises(RuntimeError, match="Network"):
        socket.socket().connect_ex(("example.invalid", 443))