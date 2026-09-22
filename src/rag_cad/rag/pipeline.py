"""Small injectable RAG shell for security and checkpoint-swap plumbing tests."""

from dataclasses import dataclass

import numpy as np

from rag_cad.operations.provenance import digest

THRESHOLD = 0.5


@dataclass(frozen=True)
class Passage:
    chunk_id: str
    sentences: tuple[str, ...]


class RAGPipeline:
    def __init__(self, retriever, generator, prompt: str):
        self.retriever = retriever
        self.generator = generator
        self.prompt = prompt

    def run(self, query: str, scorer=None, retrieved_passages=None) -> dict:
        passages = (self.retriever(query) if retrieved_passages is None else retrieved_passages)
        if scorer is not None and getattr(scorer, "threshold", THRESHOLD) != THRESHOLD:
            raise ValueError("The RAG filter threshold is fixed at 0.5 by the experimental contract")
        evidence = []
        contexts = []
        for passage in passages:
            scores = np.zeros(len(passage.sentences)) if scorer is None else np.asarray(
                scorer(query, list(passage.sentences)), dtype=float)
            if scores.shape != (len(passage.sentences),) or not np.isfinite(scores).all():
                raise ValueError("Invalid sentence probabilities")
            if ((scores < 0) | (scores > 1)).any():
                raise ValueError("Probabilities must be in [0,1]")
            retained = [index for index, score in enumerate(scores) if score <= THRESHOLD]
            removed = [index for index in range(len(scores)) if index not in retained]
            contexts.append("\n".join(passage.sentences[index] for index in retained))
            evidence.append({"chunk_id": passage.chunk_id, "scores": scores.tolist(),
                             "retained_ids": retained, "removed_ids": removed,
                             "retained_text": contexts[-1],
                             "removed_text": "\n".join(passage.sentences[index] for index in removed)})
        prompt = self.prompt.format(query=query, context="\n\n".join(contexts))
        return {"answer": self.generator(prompt), "evidence": evidence,
            "checkpoint_id": getattr(scorer, "checkpoint_id", None),
                "retrieval_hash": digest([{"id": passage.chunk_id, "sentences": passage.sentences}
                                          for passage in passages]),
                "prompt_template_hash": digest(self.prompt), "prompt_hash": digest(prompt),
                "threshold": THRESHOLD}