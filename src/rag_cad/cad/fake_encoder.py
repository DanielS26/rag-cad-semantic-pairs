"""Deterministic CPU stand-in for the frozen encoder; never a scientific substitute."""

import numpy as np

from rag_cad.cad.representation import Encoding, RepresentationConfig

FAKE_REPRESENTATION = RepresentationConfig(mode="repo_compatible", encoder_revision="a" * 40,
                                           encoder_code_revision="b" * 40, segmenter="c" * 64)


class FakeEncoder:
    """Character-valued token embeddings with JinaEncoder's call contract."""

    kind = "fake"

    def __init__(self):
        self.max_token_length = 0

    def __call__(self, text: str) -> Encoding:
        self.max_token_length = max(self.max_token_length, len(text))
        values = np.array([ord(character) / 128 for character in text], dtype=np.float32)
        hidden = np.repeat(values[:, None], 1024, axis=1) + values.mean() / 10
        return Encoding(hidden, np.ones(len(text)), [(index, index + 1) for index in range(len(text))])
