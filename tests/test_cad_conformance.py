import numpy as np
import pytest

from rag_cad.cad.representation import Encoding, build_features
from rag_cad.cad.upstream_adapter import split_units


def hand_encoder(text):
    table = {
        "Q A B": ([2, 6, 10], [(0, 1), (2, 3), (4, 5)]),
        "Q B": ([1, 3], [(0, 1), (2, 3)]),
        "Q A": ([1, 5], [(0, 1), (2, 3)]),
        "A": ([4], [(0, 1)]), "B": ([8], [(0, 1)]),
    }
    values, offsets = table[text]
    return Encoding(np.repeat(np.array(values, dtype=np.float32)[:, None], 1024, axis=1),
                    np.ones(len(values)), offsets)


def test_hand_computed_representations_and_alignment():
    repo = build_features("Q", ["A", "B"], hand_encoder, "repo_compatible")
    paper = build_features("Q", ["A", "B"], hand_encoder, "paper_exact")
    assert repo.shape == paper.shape == (2, 2048)
    np.testing.assert_array_equal(repo[:, 0], [4, 8])
    np.testing.assert_array_equal(repo[:, 1024], [4, 1])
    np.testing.assert_array_equal(paper[:, 1024], [4, 3])
    np.testing.assert_array_equal(repo, build_features("Q", ["A", "B"], hand_encoder, "repo_compatible"))
    with pytest.raises(ValueError):
        build_features("Q", ["A"], hand_encoder, "unselected")


def test_newline_roundtrip_and_literal_newlines():
    def tokenize(text):
        return [text]

    assert split_units("A\nB\\nC", tokenize) == ["A", "B", "C"]
    assert split_units("\n".join(["A", "B"]), tokenize) == ["A", "B"]