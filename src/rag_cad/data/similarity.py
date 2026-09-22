"""Deterministic lexical duplicate detection over normalised word shingles."""

import re
from collections import defaultdict
from collections.abc import Callable, Hashable, Iterable

NON_ALPHANUMERIC = re.compile(r"[^0-9a-z]+")
SHINGLE_SIZE = 3


def normalise(text: str) -> str:
    return " ".join(NON_ALPHANUMERIC.sub(" ", text.casefold()).split())


def shingles(text: str, size: int = SHINGLE_SIZE) -> frozenset[str]:
    tokens = normalise(text).split()
    if not tokens:
        return frozenset()
    if len(tokens) <= size:
        return frozenset({" ".join(tokens)})
    return frozenset(" ".join(tokens[index:index + size]) for index in range(len(tokens) - size + 1))


def jaccard(left: frozenset, right: frozenset) -> float:
    if not left and not right:
        return 1.0
    union = len(left | right)
    return len(left & right) / union if union else 0.0


def exact_duplicates(items: Iterable[tuple[Hashable, str]]) -> dict[str, list]:
    """Map each normalised text shared by several keys to those keys, in input order."""
    groups = defaultdict(list)
    for key, text in items:
        groups[normalise(text)].append(key)
    return {text: keys for text, keys in groups.items() if len(keys) > 1}


def near_duplicates(items: Iterable[tuple[Hashable, str]], threshold: float, *,
                    size: int = SHINGLE_SIZE,
                    related: Callable[[Hashable, Hashable], bool] | None = None) -> list[tuple]:
    """Exact Jaccard over word shingles for every pair sharing at least one shingle.

    Pairs are reported in input order as (key, other_key, similarity) when the
    similarity reaches the threshold and `related` (if given) accepts the pair.
    """
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not 0 < threshold <= 1:
        raise ValueError("Near-duplicate threshold must be a number in (0, 1]")
    entries = [(key, shingles(text, size)) for key, text in items]
    index = defaultdict(list)
    for position, (_, grams) in enumerate(entries):
        for gram in grams:
            index[gram].append(position)
    found = []
    for position, (key, grams) in enumerate(entries):
        shared = defaultdict(int)
        for gram in grams:
            for other in index[gram]:
                if other > position:
                    shared[other] += 1
        for other in sorted(shared):
            other_key, other_grams = entries[other]
            if related is not None and not related(key, other_key):
                continue
            similarity = shared[other] / (len(grams) + len(other_grams) - shared[other])
            if similarity >= threshold:
                found.append((key, other_key, similarity))
    return found


def near_duplicates_against(queries: Iterable[tuple[Hashable, str]],
                            corpus: Iterable[tuple[Hashable, str]], threshold: float, *,
                            size: int = SHINGLE_SIZE,
                            related: Callable[[Hashable, Hashable], bool] | None = None) -> list[tuple]:
    """Exact Jaccard of every query against every corpus item sharing a shingle with it.

    The corpus may contain the queries themselves; a query is never paired with its own key.
    Symmetric pairs among queries are reported once, from the smaller key.
    """
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not 0 < threshold <= 1:
        raise ValueError("Near-duplicate threshold must be a number in (0, 1]")
    queries = list(queries)
    query_keys = {key for key, _ in queries}
    entries = [(key, shingles(text, size)) for key, text in corpus]
    index = defaultdict(list)
    for position, (_, grams) in enumerate(entries):
        for gram in grams:
            index[gram].append(position)
    found = []
    for key, text in queries:
        grams = shingles(text, size)
        shared = defaultdict(int)
        for gram in grams:
            for position in index[gram]:
                shared[position] += 1
        for position in sorted(shared):
            other_key, other_grams = entries[position]
            if other_key == key or (other_key in query_keys and other_key < key):
                continue
            if related is not None and not related(key, other_key):
                continue
            similarity = shared[position] / (len(grams) + len(other_grams) - shared[position])
            if similarity >= threshold:
                found.append((key, other_key, similarity))
    return found
