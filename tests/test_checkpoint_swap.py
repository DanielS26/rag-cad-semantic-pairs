import pytest

from rag_cad.rag.pipeline import Passage, RAGPipeline


def test_checkpoint_swap_keeps_retrieval_and_prompt_config():
    passages = [Passage("fixture", ("Useful evidence.", "Synthetic target."))]
    pipeline = RAGPipeline(lambda query: passages, lambda prompt: prompt,
                           "Query: {query}\nContext: {context}")
    clean = pipeline.run("test")
    filtered = pipeline.run("test", lambda query, sentences: [0.5, 0.9], passages)
    assert "Synthetic target." in clean["answer"]
    assert "Synthetic target." not in filtered["answer"]
    assert "Useful evidence." in filtered["answer"]
    for key in ("retrieval_hash", "prompt_template_hash", "threshold"):
        assert clean[key] == filtered[key]
    empty = pipeline.run("test", lambda query, sentences: [1, 1], passages)
    assert empty["evidence"][0]["retained_ids"] == []
    assert "Useful evidence." not in empty["answer"]


def test_invalid_probabilities_fail():
    pipeline = RAGPipeline(lambda query: [Passage("x", ("fixture",))], str, "{context}")
    with pytest.raises(ValueError, match="probabilities"):
        pipeline.run("test", lambda query, sentences: [float("nan")])