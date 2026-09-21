"""Named, revision-pinned Jina inputs; execution always uses local files only."""

import json
import os
import shutil
import socket
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from rag_cad.config import require_sha
from rag_cad.operations.paths import local_path
from rag_cad.operations.provenance import sha256, write_json

MODEL_REPO = "jinaai/jina-embeddings-v3"
CODE_REPO = "jinaai/xlm-roberta-flash-implementation"
MODEL_FILES = ("config.json", "tokenizer.json", "tokenizer_config.json",
               "special_tokens_map.json", "model.safetensors")
CODE_FILES = ("block.py", "configuration_xlm_roberta.py", "embedding.py", "mha.py", "mlp.py",
              "modeling_lora.py", "modeling_xlm_roberta.py", "rotary.py",
              "stochastic_depth.py", "xlm_padding.py")


@contextmanager
def offline_execution():
    """Defence in depth for reviewed code, not a sandbox for hostile Python."""
    def refuse(*args, **kwargs):
        raise RuntimeError("Network is forbidden during model execution")

    with patch.dict(os.environ, {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}), \
            patch.object(socket.socket, "connect", refuse), \
            patch.object(socket.socket, "connect_ex", refuse), \
            patch.object(socket, "create_connection", refuse):
        yield


def local_config(source: dict) -> dict:
    value = dict(source)
    if "auto_map" in value:
        mapping = {}
        for key, reference in value["auto_map"].items():
            if not isinstance(reference, str):
                raise ValueError("Unexpected remote-code mapping")
            prefix = CODE_REPO + "--"
            if not reference.startswith(prefix):
                raise ValueError("Unapproved remote-code repository reference")
            local = reference[len(prefix):]
            if local.split(".")[0] + ".py" not in CODE_FILES:
                raise ValueError("Unapproved remote-code module")
            mapping[key] = local
        value["auto_map"] = mapping
    value.pop("_name_or_path", None)
    return value


def _check_bundle(root: Path, weights_revision: str, code_revision: str) -> dict:
    manifest = json.loads((root / "bundle_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("weights_revision") != weights_revision or manifest.get("code_revision") != code_revision:
        raise ValueError("Bundle revisions differ from requested weights/code pins")
    if manifest.get("model_repository") != MODEL_REPO or manifest.get("code_repository") != CODE_REPO:
        raise ValueError("Bundle repository mismatch")
    expected = set(MODEL_FILES + CODE_FILES) | {"config.original.json", "tokenizer_config.original.json"}
    if set(manifest.get("files", {})) != expected:
        raise ValueError("Incomplete or unknown bundle file inventory")
    if {path.name for path in root.iterdir()} != expected | {"bundle_manifest.json"}:
        raise ValueError("Unexpected bundle contents")
    for name, expected_hash in manifest["files"].items():
        require_sha(expected_hash, 64)
        path = root / name
        if path.is_symlink() or not path.is_file() or sha256(path) != expected_hash:
            raise ValueError("Bundle integrity check failed")
    for name in ("config", "tokenizer_config"):
        original = json.loads((root / f"{name}.original.json").read_text(encoding="utf-8"))
        derived = json.loads((root / f"{name}.json").read_text(encoding="utf-8"))
        if derived != local_config(original):
            raise ValueError("Derived local configuration differs from recorded transformation")
    return manifest


def stage_remote_code(root: Path, weights_revision: str, code_revision: str) -> Path:
    """Copy every verified code file into transformers' dynamic-module cache for this bundle.

    From a local directory, transformers copies a remote-code file plus only its direct
    relative imports, then hashes all recursive relative imports; the pinned code has
    two levels of relative imports, so loading fails with FileNotFoundError unless every
    file is already present. Only the hash-verified bundle code files are staged.
    """
    import importlib

    _check_bundle(local_path(root), weights_revision, code_revision)
    dynamic = importlib.import_module("transformers.dynamic_module_utils")
    sanitize = getattr(dynamic, "_sanitize_module_name", lambda name: name)
    relative = Path(dynamic.TRANSFORMERS_DYNAMIC_MODULE_NAME) / sanitize(root.name)
    dynamic.create_dynamic_module(relative)
    target = local_path(Path(dynamic.HF_MODULES_CACHE) / relative)
    for name in CODE_FILES:
        shutil.copyfile(root / name, target / name)
    importlib.invalidate_caches()
    return target


def prepare_bundle(root: Path, weights_revision: str, code_revision: str, *,
                   allow_network: bool = False, download=None) -> dict:
    local_path(root)
    require_sha(weights_revision)
    require_sha(code_revision)
    if root.exists():
        if root.is_symlink():
            raise ValueError("Linked model bundle is forbidden")
        return _check_bundle(root, weights_revision, code_revision)
    if allow_network is not True:
        raise ValueError("Model bundle missing; explicit network permission is required")
    if download is None:
        from huggingface_hub import hf_hub_download

        download = hf_hub_download
    cache = local_path(root.parent / "download-cache")
    partial = root.with_name(root.name + ".partial")
    partial.mkdir(parents=True, exist_ok=False)
    for repository, revision, filenames in ((MODEL_REPO, weights_revision, MODEL_FILES),
                                             (CODE_REPO, code_revision, CODE_FILES)):
        for filename in filenames:
            cached = download(repo_id=repository, filename=filename, revision=revision,
                              local_files_only=False, token=False,
                              cache_dir=str(cache))
            shutil.copyfile(cached, partial / filename)
    for name in ("config", "tokenizer_config"):
        source = partial / f"{name}.json"
        original = partial / f"{name}.original.json"
        source.rename(original)
        write_json(source, local_config(json.loads(original.read_text(encoding="utf-8"))))
    manifest = {
        "model_repository": MODEL_REPO, "code_repository": CODE_REPO,
        "weights_revision": weights_revision, "code_revision": code_revision,
        "transformation": "Local auto_map references; remove _name_or_path; retain original configs",
        "files": {path.name: sha256(path) for path in sorted(partial.iterdir())},
    }
    write_json(partial / "bundle_manifest.json", manifest)
    _check_bundle(partial, weights_revision, code_revision)
    partial.rename(root)
    return manifest