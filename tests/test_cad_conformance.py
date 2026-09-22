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


def test_representation_config_identity_and_profile_binding():
    import yaml

    from rag_cad.cad.representation import MODES, RepresentationConfig

    config = RepresentationConfig(mode="repo_compatible", encoder_revision="a" * 40,
                                  encoder_code_revision="b" * 40, segmenter="c" * 64)
    assert len(config.representation_id) == 64 and config.representation_id == config.representation_id
    other = RepresentationConfig(mode="paper_exact", encoder_revision="a" * 40,
                                 encoder_code_revision="b" * 40, segmenter="c" * 64)
    assert other.representation_id != config.representation_id
    assert config.as_dict()["representation_id"] == config.representation_id
    np.testing.assert_array_equal(config.build("Q", ["A", "B"], hand_encoder),
                                  build_features("Q", ["A", "B"], hand_encoder, "repo_compatible"))
    np.testing.assert_array_equal(other.build("Q", ["A", "B"], hand_encoder),
                                  build_features("Q", ["A", "B"], hand_encoder, "paper_exact"))
    for bad in ({"mode": "unselected"}, {"encoder_revision": "short"}, {"segmenter": "x"}, {"dtype": "float16"},
                {"attention": "flash"}):
        with pytest.raises(ValueError):
            RepresentationConfig(**({"mode": "repo_compatible", "encoder_revision": "a" * 40,
                                     "encoder_code_revision": "b" * 40, "segmenter": "c" * 64} | bad))
    profile_path = __import__("pathlib").Path(__file__).resolve().parents[1] / "configs/environments/colab_tested.yaml"
    profile = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    bound = RepresentationConfig.from_profile(profile)
    assert bound.mode == "repo_compatible" and bound.encoder_revision == profile["expected"]["encoder_revision"]
    assert RepresentationConfig.from_profile(profile, mode="paper_exact").mode == "paper_exact"
    assert set(MODES) == {"repo_compatible", "paper_exact"}


def test_fake_mode_comparison_reports_both_modes_without_choosing():
    from rag_cad.cad.fake_encoder import FakeEncoder
    from rag_cad.operations.smoke import QUERY, SENTENCES, compare_modes

    def reference(features):
        positive = 1 / (1 + np.exp(-features[:, 0]))
        return np.column_stack([1 - positive, positive])

    report = compare_modes(FakeEncoder(), reference, QUERY, SENTENCES, atol=1e-6, rtol=1e-6)
    assert set(report["modes"]) == {"repo_compatible", "paper_exact"}
    for entry in report["modes"].values():
        assert entry["shape"] == [3, 2048] and entry["finite"] and entry["deterministic"]
        assert len(entry["reference_probabilities"]) == 3 and entry["seconds"] >= 0
    assert report["isolated_block_identical"] is True
    assert report["contextual_max_abs_difference"] > 0
    assert report["primary_mode_selected"] is False and isinstance(report["reference_decisions_agree"], bool)