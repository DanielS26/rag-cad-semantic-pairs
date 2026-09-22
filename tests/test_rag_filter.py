import json

import numpy as np
import pytest

from rag_cad.cad.fake_encoder import FAKE_REPRESENTATION, FakeEncoder
from rag_cad.cad.feature_builder import FeatureBuilder
from rag_cad.cad.scorer import CADScorer, ScoredPassage, synthetic_checkpoint
from rag_cad.cad.upstream_adapter import STATE_SHAPES
from rag_cad.operations.provenance import canonical_json, sha256
from rag_cad.rag.pipeline import Passage, RAGPipeline

CONTRACT = {"representation_id": "synthetic-smoke", "encoder_revision": "a" * 40,
            "encoder_code_revision": "b" * 40}
PASSAGE = "Useful evidence.\nSynthetic target.\nA synthetic conclusion."


def first_column(values):
    def features(query, sentences):
        matrix = np.zeros((len(sentences), 2048), dtype=np.float32)
        matrix[:, 0] = values[:len(sentences)]
        return matrix

    return features


def newline_tokenize(text):
    return [text]


def test_three_sentence_passage_yields_scores_and_retained_removed_text(tmp_path):
    path = tmp_path / "head.npz"
    synthetic_checkpoint(path, inverted=False, **CONTRACT)
    scorer = CADScorer(path, sha256(path), first_column([0, 1, 0]), synthetic_only=True, **CONTRACT)
    scored = scorer.score_passage("Summarise.", PASSAGE, tokenize=newline_tokenize)
    assert isinstance(scored, ScoredPassage)
    assert scored.sentences == ("Useful evidence.", "Synthetic target.", "A synthetic conclusion.")
    assert len(scored.probabilities) == 3 and scored.decisions == (False, True, False)
    assert scored.retained_ids == (0, 2) and scored.removed_ids == (1,)
    assert scored.retained_text == "Useful evidence.\nA synthetic conclusion."
    assert scored.removed_text == "Synthetic target."
    assert scored.threshold == 0.5 and scored.checkpoint_id == sha256(path)
    assert scored.representation_id == "synthetic-smoke" and scored.passage == PASSAGE
    assert scored.segmentation_seconds >= 0 and scored.scoring_seconds >= 0
    json.loads(canonical_json(scored.as_dict()))
    empty = scorer.score_passage("Summarise.", "   ", tokenize=newline_tokenize)
    assert empty.sentences == () and empty.retained_text == "" and empty.removed_text == ""


def test_runtime_scoring_uses_the_training_feature_implementation(tmp_path):
    path = tmp_path / "head.npz"
    contract = {"representation_id": FAKE_REPRESENTATION.representation_id,
                "encoder_revision": FAKE_REPRESENTATION.encoder_revision,
                "encoder_code_revision": FAKE_REPRESENTATION.encoder_code_revision}
    synthetic_checkpoint(path, inverted=False, **contract)
    scorer = CADScorer.from_representation(path, sha256(path), FAKE_REPRESENTATION, FakeEncoder(),
                                           synthetic_only=True)
    scored = scorer.score_passage("Summarise.", PASSAGE, tokenize=newline_tokenize)
    assert len(scored.probabilities) == 3 and all(0 <= value <= 1 for value in scored.probabilities)
    builder = FeatureBuilder(FAKE_REPRESENTATION, FakeEncoder(), feature_environment_id="fake-env",
                             commit="f" * 40, config_sha256="0" * 64)
    np.testing.assert_array_equal(builder.features("Summarise.", list(scored.sentences)),
                                  scorer.feature_builder("Summarise.", list(scored.sentences)))
    assert scorer.representation_id == FAKE_REPRESENTATION.representation_id


def test_incompatible_checkpoints_raise_clear_errors(tmp_path):
    path = tmp_path / "head.npz"
    synthetic_checkpoint(path, inverted=False, **CONTRACT)
    with pytest.raises(ValueError, match="mismatch: representation_id"):
        CADScorer(path, sha256(path), first_column([0]), synthetic_only=True,
                  **(CONTRACT | {"representation_id": "other"}))
    with pytest.raises(ValueError, match="threshold"):
        CADScorer(path, sha256(path), first_column([0]), synthetic_only=True, threshold=0.7, **CONTRACT)
    narrow = tmp_path / "narrow.npz"
    state = {name: np.zeros(shape, dtype=np.float32) for name, shape in STATE_SHAPES.items()}
    metadata = {"format": "synthetic-smoke-v1", "input_dim": 1024, "d_hid": 256, "dropout": 0.3,
                "best_threshold": 0.5, **CONTRACT}
    with narrow.open("xb") as handle:
        np.savez_compressed(handle, metadata=json.dumps(metadata), **state)
    with pytest.raises(ValueError, match="Incompatible checkpoint metadata: input_dim"):
        CADScorer(narrow, sha256(narrow), first_column([0]), synthetic_only=True, **CONTRACT)
    with pytest.raises(ValueError, match="hash mismatch"):
        CADScorer(path, "0" * 64, first_column([0]), synthetic_only=True, **CONTRACT)


def test_pipeline_logs_retained_and_removed_text_and_never_leaks_removed(tmp_path):
    path = tmp_path / "head.npz"
    synthetic_checkpoint(path, inverted=False, **CONTRACT)
    scorer = CADScorer(path, sha256(path), first_column([0, 1, 0]), synthetic_only=True, **CONTRACT)
    passages = [Passage("chunk", tuple(PASSAGE.split("\n")))]
    received = []
    pipeline = RAGPipeline(lambda query: passages, lambda prompt: received.append(prompt) or "answer",
                           "Query: {query}\nContext: {context}")
    result = pipeline.run("Summarise.", scorer, passages)
    evidence = result["evidence"][0]
    assert evidence["retained_text"] == "Useful evidence.\nA synthetic conclusion."
    assert evidence["removed_text"] == "Synthetic target."
    assert "Synthetic target." not in received[-1] and "Useful evidence." in received[-1]
    everything = pipeline.run("Summarise.", lambda query, sentences: [1.0] * len(sentences), passages)
    assert everything["evidence"][0]["retained_text"] == "" and "Context: " in received[-1]
    assert everything["answer"] == "answer"
    with pytest.raises(ValueError, match="threshold"):
        pipeline.run("Summarise.", type("Odd", (), {"threshold": 0.3,
                                                   "__call__": lambda self, q, s: [0.0] * len(s)})(), passages)
