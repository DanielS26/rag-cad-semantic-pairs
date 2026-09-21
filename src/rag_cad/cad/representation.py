"""CAD representation interpretations, adapted from pinned detector/defense.py.

Upstream source and MIT licence are retained. No primary interpretation is selected.
"""

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from rag_cad.cad.model_bundle import offline_execution, prepare_bundle, stage_remote_code


@dataclass
class Encoding:
    hidden: np.ndarray
    attention: np.ndarray
    offsets: list[tuple[int, int]]


def pool(encoding: Encoding, keep: list[bool]) -> np.ndarray:
    mask = np.asarray(keep, dtype=bool) & encoding.attention.astype(bool)
    return encoding.hidden[mask].mean(axis=0) if mask.any() else encoding.hidden.mean(axis=0)


def build_features(query: str, sentences: list[str], encode, mode: str) -> np.ndarray:
    if mode not in {"repo_compatible", "paper_exact"}:
        raise ValueError("Representation mode must be explicit")
    if not sentences:
        return np.empty((0, 2048), dtype=np.float32)
    if any(not isinstance(text, str) or not text.strip() for text in sentences):
        raise ValueError("Sentence units must be nonempty strings")
    prefix = query.strip() + " " if query.strip() else ""
    full = prefix + " ".join(sentences)
    full_encoding = encode(full)
    position = len(prefix)
    features = []
    for index, sentence in enumerate(sentences):
        start, end = position, position + len(sentence)
        position = end + 1
        standalone = encode(sentence)
        isolated = pool(standalone, [True] * len(standalone.hidden))
        keep = ([not (left < end and right > start) for left, right in full_encoding.offsets]
                if mode == "repo_compatible" else [True] * len(full_encoding.hidden))
        with_target = pool(full_encoding, keep)
        rest = prefix + " ".join(sentences[:index] + sentences[index + 1:])
        removed = encode(rest if rest.strip() else " ")
        without_target = pool(removed, [True] * len(removed.hidden))
        features.append(np.concatenate([isolated, with_target - without_target]))
    result = np.asarray(features, dtype=np.float32)
    if result.shape != (len(sentences), 2048) or not np.isfinite(result).all():
        raise ValueError("Invalid CAD feature shape or nonfinite values")
    return result


class JinaEncoder:
    """Only constructed behind an approved real-execution preflight."""

    def __init__(self, weights_revision: str, code_revision: str, bundle: Path, *,
                 allow_network: bool = False, allow_remote_code: bool = False, progress=None):
        if allow_remote_code is not True:
            raise ValueError("Explicit reviewed remote-code permission is required")
        progress = progress or (lambda step: None)
        self.bundle_manifest = prepare_bundle(bundle, weights_revision, code_revision,
                                              allow_network=allow_network)
        progress("model_bundle_ready")
        import torch
        from transformers import AutoModel, AutoTokenizer

        self.torch = torch
        self.max_token_length = 0
        stage_remote_code(bundle, weights_revision, code_revision)
        progress("remote_code_staged")
        with offline_execution():
            self.tokenizer = AutoTokenizer.from_pretrained(
                str(bundle.resolve()), local_files_only=True, trust_remote_code=False,
            )
            progress("tokenizer_loaded")
            self.model = AutoModel.from_pretrained(
                str(bundle.resolve()), local_files_only=True, trust_remote_code=True,
                torch_dtype=torch.float32, use_safetensors=True, use_flash_attn=False,
            ).to("cuda").eval()
            progress("model_loaded")

    def __call__(self, text: str) -> Encoding:
        with offline_execution():
            inputs = self.tokenizer(text, return_tensors="pt", return_offsets_mapping=True,
                                    truncation=False)
        offsets = inputs.pop("offset_mapping")[0].tolist()
        if inputs["input_ids"].shape[1] > 8192:
            raise ValueError("Smoke input exceeds encoder token limit; no silent truncation")
        self.max_token_length = max(self.max_token_length, inputs["input_ids"].shape[1])
        inputs = {name: value.to("cuda") for name, value in inputs.items()}
        with offline_execution(), self.torch.no_grad():
            hidden = self.model(**inputs).last_hidden_state[0].float().cpu().numpy()
        return Encoding(hidden, inputs["attention_mask"][0].cpu().numpy(), offsets)