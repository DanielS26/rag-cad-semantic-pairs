"""CAD representation interpretations, adapted from pinned detector/defense.py.

Upstream source and MIT licence are retained. No primary interpretation is selected.
"""

from dataclasses import dataclass

import numpy as np

from rag_cad.config import require_sha


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

    def __init__(self, revision: str):
        require_sha(revision)
        import torch
        from transformers import AutoModel, AutoTokenizer

        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(
            "jinaai/jina-embeddings-v3", revision=revision,
            code_revision=revision, trust_remote_code=True,
        )
        self.model = AutoModel.from_pretrained(
            "jinaai/jina-embeddings-v3", revision=revision,
            code_revision=revision, trust_remote_code=True, torch_dtype=torch.float32,
        ).to("cuda").eval()

    def __call__(self, text: str) -> Encoding:
        inputs = self.tokenizer(text, return_tensors="pt", return_offsets_mapping=True,
                                truncation=False)
        offsets = inputs.pop("offset_mapping")[0].tolist()
        if inputs["input_ids"].shape[1] > 8192:
            raise ValueError("Smoke input exceeds encoder token limit; no silent truncation")
        inputs = {name: value.to("cuda") for name, value in inputs.items()}
        with self.torch.no_grad():
            hidden = self.model(**inputs).last_hidden_state[0].float().cpu().numpy()
        return Encoding(hidden, inputs["attention_mask"][0].cpu().numpy(), offsets)