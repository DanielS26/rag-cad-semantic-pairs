"""CAD representation interpretations, adapted from pinned detector/defense.py.

Upstream source and MIT licence are retained. repo_compatible is the primary interpretation
(D-20261004-13); paper_exact is kept as a documented secondary variant.
"""

from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from rag_cad.cad.model_bundle import offline_execution, prepare_bundle, stage_remote_code
from rag_cad.config import require_sha
from rag_cad.operations.provenance import digest

MODES = ("repo_compatible", "paper_exact")


@dataclass
class Encoding:
    hidden: np.ndarray
    attention: np.ndarray
    offsets: list[tuple[int, int]]


@dataclass(frozen=True)
class RepresentationConfig:
    """Everything that determines a feature vector's meaning, hashed into one representation_id.

    Training-time feature builds and runtime scoring must construct features through the
    same instance so both call the identical selected implementation.
    """

    mode: str
    encoder_revision: str
    encoder_code_revision: str
    segmenter: str
    dtype: str = "float32"
    attention: str = "native"

    def __post_init__(self):
        if self.mode not in MODES:
            raise ValueError("Representation mode must be explicit")
        require_sha(self.encoder_revision)
        require_sha(self.encoder_code_revision)
        require_sha(self.segmenter, 64)
        if self.dtype != "float32" or self.attention != "native":
            raise ValueError("Only the contracted float32 native-attention representation is supported")

    @classmethod
    def from_profile(cls, profile: dict, *, mode: str | None = None) -> "RepresentationConfig":
        expected = profile["expected"]
        return cls(mode=expected["representation"] if mode is None else mode,
                   encoder_revision=expected["encoder_revision"],
                   encoder_code_revision=expected["encoder_code_revision"],
                   segmenter=expected["segmenter"], dtype=expected["dtype"], attention=expected["attention"])

    @property
    def representation_id(self) -> str:
        return digest(asdict(self))

    def as_dict(self) -> dict:
        return asdict(self) | {"representation_id": self.representation_id}

    def build(self, query: str, sentences: list[str], encode) -> np.ndarray:
        return build_features(query, sentences, encode, self.mode)


def pool(encoding: Encoding, keep: list[bool]) -> np.ndarray:
    mask = np.asarray(keep, dtype=bool) & encoding.attention.astype(bool)
    return encoding.hidden[mask].mean(axis=0) if mask.any() else encoding.hidden.mean(axis=0)


def build_mode_features(query: str, sentences: list[str], encode) -> dict[str, np.ndarray]:
    """Both representation modes from one set of encoder passes.

    The modes share every encoder call (the full passage, each sentence alone and the passage
    with each sentence removed) and differ only in which tokens of the full passage are pooled
    for the first contextual term, so computing both costs one mode's encoder time.
    """
    if not sentences:
        return {mode: np.empty((0, 2048), dtype=np.float32) for mode in MODES}
    if any(not isinstance(text, str) or not text.strip() for text in sentences):
        raise ValueError("Sentence units must be nonempty strings")
    prefix = query.strip() + " " if query.strip() else ""
    full = prefix + " ".join(sentences)
    full_encoding = encode(full)
    everything = [True] * len(full_encoding.hidden)
    position = len(prefix)
    features = {mode: [] for mode in MODES}
    for index, sentence in enumerate(sentences):
        start, end = position, position + len(sentence)
        position = end + 1
        standalone = encode(sentence)
        isolated = pool(standalone, [True] * len(standalone.hidden))
        outside = [not (left < end and right > start) for left, right in full_encoding.offsets]
        rest = prefix + " ".join(sentences[:index] + sentences[index + 1:])
        removed = encode(rest if rest.strip() else " ")
        without_target = pool(removed, [True] * len(removed.hidden))
        for mode, keep in (("repo_compatible", outside), ("paper_exact", everything)):
            contextual = pool(full_encoding, keep) - without_target
            features[mode].append(np.concatenate([isolated, contextual]))
    result = {}
    for mode in MODES:
        values = np.asarray(features[mode], dtype=np.float32)
        if values.shape != (len(sentences), 2048) or not np.isfinite(values).all():
            raise ValueError("Invalid CAD feature shape or nonfinite values")
        result[mode] = values
    return result


def build_features(query: str, sentences: list[str], encode, mode: str) -> np.ndarray:
    if mode not in MODES:
        raise ValueError("Representation mode must be explicit")
    return build_mode_features(query, sentences, encode)[mode]


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