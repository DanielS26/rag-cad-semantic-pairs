"""Document store and retriever of the Phase 8 harness (D-20261017-58 (b)).

A round's store holds the 160 records of its 40 held-out families and a fixed set of benign
upstream distractors. Every document is the mean of its sentence embeddings, and a sentence
embedding is the standalone half of the cached CAD feature (the first 1,024 columns: the
sentence encoded alone and mean-pooled, the same in both representation modes). Nothing is
encoded here.

No cache holds an embedding of a query: the CAD features encode the query only as a prefix of
the whole passage and keep no pooled query vector, and the encoder is not called. A query is
therefore placed in the embedding space through the store's own sentences: the query field is
matched against every store sentence by TF-IDF cosine (terms from the project's normalise), and
the query vector is the mean embedding of the five best-matching sentences. A query with no term
in common with any store sentence falls back to the store centroid, and the count is reported.
Retrieval is exact cosine search over the unit document vectors, the top five per query, ties
broken by store order; it depends only on the store, so every gate condition sees identical
retrievals.

Distractors: the released CAD test holds no wholly benign record (every record carries an
injection), so a distractor is the benign remainder of a leak-excluded released-test record (its
label-0 sentences in their original order). Records whose remainders are the same text after
normalisation are one candidate (one representative drawn per text), and the set is drawn once
with seed 764, the same in every round.
"""

import math
from collections import Counter
from dataclasses import dataclass, field

import numpy as np

from rag_cad.data.similarity import normalise
from rag_cad.operations.provenance import digest

EMBEDDING_COLUMNS = 1024
TOP_K = 5
QUERY_SENTENCES = 5
DISTRACTOR_SEED = 764
FAMILY_KINDS = ("malicious", "twin", "random_control", "keyword_control")
DISTRACTOR = "distractor"
KINDS = FAMILY_KINDS + (DISTRACTOR,)
LEXICAL = "lexical"
CENTROID = "store_centroid"


def sentence_embeddings(features) -> np.ndarray:
    """The standalone sentence embedding of each CAD feature row (columns 0 to 1,023), float64."""
    features = np.asarray(features)
    if features.ndim != 2 or features.shape[1] != 2 * EMBEDDING_COLUMNS:
        raise ValueError("CAD features must have 2,048 columns")
    return features[:, :EMBEDDING_COLUMNS].astype(np.float64)


def unit(vector: np.ndarray, name: str) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if not math.isfinite(norm) or norm == 0.0:
        raise ValueError(f"{name} has a zero or non-finite embedding")
    return vector / norm


@dataclass(frozen=True, eq=False)
class Document:
    """One retrievable record: its sentences in order, their labels, target flags, texts and
    embeddings; for a twin, the sentence ids that carry its cue (empty for a query cue)."""

    doc_id: str
    kind: str
    sentence_ids: tuple[int, ...]
    labels: tuple[int, ...]
    targets: tuple[bool, ...]
    texts: tuple[str, ...]
    embeddings: np.ndarray
    group_id: str | None = None
    query: str | None = None
    cue_ids: frozenset = frozenset()
    semantic_role: str | None = None
    cue_position: str | None = None

    def __post_init__(self):
        count = len(self.sentence_ids)
        if self.kind not in KINDS:
            raise ValueError(f"Unknown document kind: {self.kind}")
        if count == 0 or len(set(self.sentence_ids)) != count:
            raise ValueError(f"Document {self.doc_id} needs distinct sentence ids")
        if any(len(values) != count for values in (self.labels, self.targets, self.texts)):
            raise ValueError(f"Document {self.doc_id} is misaligned")
        if np.shape(self.embeddings) != (count, EMBEDDING_COLUMNS):
            raise ValueError(f"Document {self.doc_id} embeddings are misaligned")
        if not set(self.cue_ids) <= set(self.sentence_ids) or sum(self.targets) > 1:
            raise ValueError(f"Document {self.doc_id} has an unknown cue or several targets")
        if self.kind == DISTRACTOR and any(self.labels):
            raise ValueError(f"Distractor {self.doc_id} holds a malicious sentence")

    @property
    def target_id(self) -> int | None:
        found = [sid for sid, target in zip(self.sentence_ids, self.targets) if target]
        return found[0] if found else None

    def vector(self) -> np.ndarray:
        return unit(np.asarray(self.embeddings, dtype=np.float64).mean(axis=0), self.doc_id)


@dataclass
class Store:
    round: int
    documents: list[Document]
    matrix: np.ndarray = field(init=False, repr=False)
    index: dict = field(init=False, repr=False)

    def __post_init__(self):
        ids = [document.doc_id for document in self.documents]
        if not ids or len(set(ids)) != len(ids):
            raise ValueError("Store document ids must be unique and present")
        self.matrix = np.stack([document.vector() for document in self.documents])
        self.index = {doc_id: position for position, doc_id in enumerate(ids)}

    def composition(self) -> dict:
        kinds = Counter(document.kind for document in self.documents)
        sentences = Counter()
        for document in self.documents:
            sentences[document.kind] += len(document.sentence_ids)
        return {"round": self.round, "documents": len(self.documents),
                "by_kind": {kind: kinds.get(kind, 0) for kind in KINDS},
                "families": len({d.group_id for d in self.documents if d.kind != DISTRACTOR}),
                "sentences": sum(sentences.values()),
                "sentences_by_kind": {kind: sentences.get(kind, 0) for kind in KINDS},
                "distractor_ids": sorted(d.doc_id for d in self.documents if d.kind == DISTRACTOR),
                "digest": digest([[d.doc_id, list(d.sentence_ids)] for d in self.documents])}


def build_store(round_number: int, family_documents: list[Document],
                distractors: list[Document]) -> Store:
    """The round's family records (each held-out family whole: all four kinds) and the distractors."""
    groups: dict[str, list[str]] = {}
    for document in family_documents:
        if document.kind not in FAMILY_KINDS or document.group_id is None:
            raise ValueError(f"{document.doc_id} is not a family record")
        groups.setdefault(document.group_id, []).append(document.kind)
    for group, kinds in groups.items():
        if sorted(kinds) != sorted(FAMILY_KINDS):
            raise ValueError(f"Round {round_number}: family {group} is not whole in the store")
    if any(document.kind != DISTRACTOR for document in distractors):
        raise ValueError("Distractors must be distractor documents")
    ordered = sorted(family_documents, key=lambda d: d.doc_id) + sorted(distractors,
                                                                         key=lambda d: d.doc_id)
    return Store(round_number, ordered)


def select_distractors(records: list[dict], excluded: set[str], count: int,
                       seed: int = DISTRACTOR_SEED) -> tuple[list[dict], dict]:
    """The benign remainders of the released-test records outside the excluded (leaked) set, one
    per distinct normalised text, drawn once with the seed; fewer when fewer exist."""
    if isinstance(count, bool) or type(count) is not int or count < 1:
        raise ValueError("The distractor count must be a positive integer")
    candidates: dict[str, list[dict]] = {}
    considered = 0
    for record in sorted(records, key=lambda r: r["record_id"]):
        if record["record_id"] in excluded:
            continue
        considered += 1
        kept = [s for s in record["sentences"] if s["label"] == 0]
        key = normalise(" ".join(s["text"] for s in kept))
        if key:
            candidates.setdefault(key, []).append(
                {"record_id": record["record_id"], "sentence_ids": [s["sentence_id"] for s in kept]})
    keys = sorted(candidates)
    rng = np.random.default_rng(seed)
    chosen = []
    for position in rng.permutation(len(keys))[:count]:
        members = candidates[keys[int(position)]]
        chosen.append(members[int(rng.integers(len(members)))])
    chosen.sort(key=lambda item: item["record_id"])
    return chosen, {"records": len(records), "excluded": len(excluded & {r["record_id"] for r in records}),
                    "candidate_records": considered, "distinct_benign_remainders": len(keys),
                    "requested": count, "chosen": len(chosen), "capped": len(chosen) < count,
                    "seed": seed, "chosen_ids": [item["record_id"] for item in chosen]}


class LexicalIndex:
    """TF-IDF vectors of texts (terms from normalise, idf log((1 + n) / (1 + df)), so a term in
    every text weighs zero); used only to place a query among the store's sentences."""

    def __init__(self, texts: list[str]):
        tokens = [normalise(text).split() for text in texts]
        frequency = Counter(term for terms in tokens for term in set(terms))
        total = len(texts)
        self.vocabulary = {term: position for position, term in enumerate(sorted(frequency))}
        self.idf = np.array([math.log((1 + total) / (1 + frequency[term]))
                             for term in sorted(frequency)], dtype=np.float64)
        self.matrix = np.stack([self.vector(terms) for terms in tokens]) if tokens else None

    def vector(self, terms: list[str]) -> np.ndarray:
        values = np.zeros(len(self.vocabulary), dtype=np.float64)
        for term in terms:
            if term in self.vocabulary:
                values[self.vocabulary[term]] += 1.0
        values *= self.idf
        norm = float(np.linalg.norm(values))
        return values / norm if norm > 0 else values

    def similarities(self, text: str) -> np.ndarray:
        return self.matrix @ self.vector(normalise(text).split())


def query_vectors(store: Store, queries: list[tuple[str, str]],
                  sentences: int = QUERY_SENTENCES) -> tuple[np.ndarray, list[dict]]:
    """Each query's unit vector: the mean embedding of the store sentences that match its text
    best by TF-IDF cosine (positive matches only, ties by store order), else the store centroid."""
    places = [(document, position) for document in store.documents
              for position in range(len(document.sentence_ids))]
    embeddings = np.concatenate([np.asarray(d.embeddings, dtype=np.float64) for d in store.documents])
    index = LexicalIndex([document.texts[position] for document, position in places])
    vectors, details = [], []
    for query_id, text in queries:
        similarity = index.similarities(text)
        order = np.argsort(-similarity, kind="stable")[:sentences]
        chosen = [int(i) for i in order if similarity[i] > 0]
        if chosen:
            vector, source = embeddings[chosen].mean(axis=0), LEXICAL
        else:
            vector, source = embeddings.mean(axis=0), CENTROID
        vectors.append(unit(vector, f"query {query_id}"))
        details.append({"query_id": query_id, "source": source,
                        "matched": [[places[i][0].doc_id, places[i][0].sentence_ids[places[i][1]],
                                     round(float(similarity[i]), 6)] for i in chosen]})
    return np.stack(vectors), details


@dataclass(frozen=True)
class Retrieval:
    """The top documents of every query of a round; the same object serves every condition."""

    round: int
    query_ids: tuple[str, ...]
    top: tuple[tuple[str, ...], ...]
    scores: tuple[tuple[float, ...], ...]
    own_rank: tuple[int, ...]
    sources: tuple[str, ...]
    details: tuple[dict, ...] = field(repr=False, compare=False)

    @property
    def digest(self) -> str:
        return digest({"round": self.round, "queries": list(self.query_ids),
                       "top": [list(top) for top in self.top]})

    def facts(self, store: Store, k: int = TOP_K) -> dict:
        kinds = Counter(store.documents[store.index[d]].kind for top in self.top for d in top)
        own_family = [store.documents[store.index[d]].group_id == store.documents[store.index[q]].group_id
                      for q, top in zip(self.query_ids, self.top) for d in top]
        ranks = np.asarray(self.own_rank, dtype=float)
        return {"round": self.round, "queries": len(self.query_ids), "top_k": k,
                "hit_at_k": round(float((ranks <= k).mean()), 6),
                "mean_rank": round(float(ranks.mean()), 6), "median_rank": float(np.median(ranks)),
                "slots": int(sum(len(top) for top in self.top)),
                "slots_by_kind": {kind: kinds.get(kind, 0) for kind in KINDS},
                "own_family_slot_share": round(float(np.mean(own_family)), 6),
                "centroid_fallback_queries": sum(source == CENTROID for source in self.sources),
                "digest": self.digest}


def retrieve(store: Store, queries: list[tuple[str, str]], k: int = TOP_K,
             sentences: int = QUERY_SENTENCES) -> Retrieval:
    """Exact cosine search: the top k documents per query; the query id names its own record."""
    if not queries or any(query_id not in store.index for query_id, _ in queries):
        raise ValueError("Every query must name a record of the store")
    if k < 1 or k > len(store.documents):
        raise ValueError("Top k must lie between one and the store size")
    vectors, details = query_vectors(store, queries, sentences)
    scores = vectors @ store.matrix.T
    ids = [document.doc_id for document in store.documents]
    top, top_scores, ranks = [], [], []
    for (query_id, _), row in zip(queries, scores):
        order = np.argsort(-row, kind="stable")
        top.append(tuple(ids[i] for i in order[:k]))
        top_scores.append(tuple(round(float(row[i]), 8) for i in order[:k]))
        ranks.append(int(np.flatnonzero(order == store.index[query_id])[0]) + 1)
    return Retrieval(store.round, tuple(q for q, _ in queries), tuple(top), tuple(top_scores),
                     tuple(ranks), tuple(d["source"] for d in details), tuple(details))
