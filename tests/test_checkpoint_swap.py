import numpy as np
import pytest

from rag_cad.cad.scorer import CADScorer, synthetic_checkpoint
from rag_cad.operations.provenance import sha256
from rag_cad.rag.pipeline import Passage, RAGPipeline


def test_checkpoint_swap_keeps_retrieval_and_prompt_config(tmp_path):
    contract = {"representation_id": "synthetic-smoke", "encoder_revision": "a" * 40,
                "encoder_code_revision": "b" * 40}

    def features(query, sentences):
        values = np.zeros((len(sentences), 2048), dtype=np.float32)
        values[:, 0] = np.arange(len(sentences))
        return values

    paths = [tmp_path / "first.npz", tmp_path / "second.npz"]
    for index, path in enumerate(paths):
        synthetic_checkpoint(path, inverted=bool(index), **contract)
    scorers = [CADScorer(path, sha256(path), features, synthetic_only=True, **contract) for path in paths]
    passages = [Passage("fixture", ("Useful evidence.", "Synthetic target."))]
    pipeline = RAGPipeline(lambda query: passages, lambda prompt: prompt,
                           "Query: {query}\nContext: {context}")
    clean = pipeline.run("test")
    filtered = pipeline.run("test", scorers[0], passages)
    swapped = pipeline.run("test", scorers[1], passages)
    assert "Synthetic target." in clean["answer"]
    assert "Synthetic target." not in filtered["answer"]
    assert "Useful evidence." in filtered["answer"]
    for key in ("retrieval_hash", "prompt_template_hash", "threshold"):
        assert clean[key] == filtered[key] == swapped[key]
    assert filtered["checkpoint_id"] != swapped["checkpoint_id"]
    assert "Useful evidence." not in swapped["answer"]
    assert "Synthetic target." in swapped["answer"]
    reloaded = CADScorer(paths[0], sha256(paths[0]), features, synthetic_only=True, **contract)
    assert pipeline.run("test", reloaded, passages) == filtered
    with pytest.raises(ValueError, match="mismatch"):
        CADScorer(paths[0], sha256(paths[0]), features, synthetic_only=True,
                  **(contract | {"encoder_code_revision": "c" * 40}))
    empty = pipeline.run("test", lambda query, sentences: [1, 1], passages)
    assert empty["evidence"][0]["retained_ids"] == []
    assert "Useful evidence." not in empty["answer"]


def test_invalid_probabilities_fail():
    pipeline = RAGPipeline(lambda query: [Passage("x", ("fixture",))], str, "{context}")
    with pytest.raises(ValueError, match="probabilities"):
        pipeline.run("test", lambda query, sentences: [float("nan")])