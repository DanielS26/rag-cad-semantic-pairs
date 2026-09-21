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


def fake_dynamic_modules(tmp_path, monkeypatch):
    """Mimic transformers' local-directory copy rules: only direct relative imports are copied."""
    cache = tmp_path / "modules"
    created = []

    def create_dynamic_module(name):
        path = cache / name
        path.mkdir(parents=True, exist_ok=True)
        (path / "__init__.py").touch()
        created.append(str(name))

    dynamic = SimpleNamespace(HF_MODULES_CACHE=str(cache), TRANSFORMERS_DYNAMIC_MODULE_NAME="transformers_modules",
                              _sanitize_module_name=lambda name: name.replace("-", "_hyphen_"),
                              create_dynamic_module=create_dynamic_module)
    monkeypatch.setitem(sys.modules, "transformers.dynamic_module_utils", dynamic)
    return cache, created


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
    fake_dynamic_modules(tmp_path, monkeypatch)
    representation.JinaEncoder(WEIGHTS, CODE, bundle, allow_remote_code=True)
    assert all(path == str(bundle.resolve()) for path, _ in loads)
    assert loads[1][1]["use_flash_attn"] is False
    with offline_execution(), pytest.raises(RuntimeError, match="Network"):
        socket.socket().connect_ex(("example.invalid", 443))

def test_encoder_reports_fixed_progress_steps(tmp_path, monkeypatch):
    calls, download = fake_downloads(tmp_path)
    bundle = tmp_path / "bundle"
    prepare_bundle(bundle, WEIGHTS, CODE, allow_network=True, download=download)

    class Auto:
        @classmethod
        def from_pretrained(cls, path, **kwargs):
            return cls()

        def to(self, device):
            return self

        def eval(self):
            return self

    steps = []
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(float32="float32"))
    monkeypatch.setitem(sys.modules, "transformers", SimpleNamespace(AutoModel=Auto, AutoTokenizer=Auto))
    fake_dynamic_modules(tmp_path, monkeypatch)
    representation.JinaEncoder(WEIGHTS, CODE, bundle, allow_remote_code=True, progress=steps.append)
    assert steps == ["model_bundle_ready", "remote_code_staged", "tokenizer_loaded", "model_loaded"]


def test_every_verified_code_file_is_staged_for_nested_relative_imports(tmp_path, monkeypatch):
    import hashlib

    from rag_cad.cad.model_bundle import stage_remote_code

    calls, download = fake_downloads(tmp_path)
    bundle = tmp_path / "jina-bundle"
    prepare_bundle(bundle, WEIGHTS, CODE, allow_network=True, download=download)
    cache, created = fake_dynamic_modules(tmp_path, monkeypatch)
    target = stage_remote_code(bundle, WEIGHTS, CODE)
    assert target == (cache / "transformers_modules" / "jina_hyphen_bundle").resolve()
    assert created == ["transformers_modules/jina_hyphen_bundle".replace("/", __import__("os").sep)]
    staged = {path.name for path in target.iterdir()} - {"__init__.py"}
    assert staged == set(CODE_FILES)
    for name in CODE_FILES:
        assert hashlib.sha256((target / name).read_bytes()).hexdigest() == hashlib.sha256((bundle / name).read_bytes()).hexdigest()
    (bundle / "mha.py").write_text("tampered", encoding="utf-8")
    with pytest.raises(ValueError, match="integrity"):
        stage_remote_code(bundle, WEIGHTS, CODE)
    with pytest.raises(ValueError, match="revisions"):
        stage_remote_code(bundle, "f" * 40, CODE)
