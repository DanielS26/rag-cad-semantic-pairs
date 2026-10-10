"""CPU post-hoc analysis of a published m0 artefact: released-test metrics with leaked records
excluded, and the benign rows every head flags.

Reads only the restored artefact's adapted records and prediction files; no model, feature
or GPU access. The leaked set is derived from the records with the project's own similarity,
not read from the capped example lists of the stage report.
"""

from collections import Counter
from pathlib import Path

import numpy as np

from rag_cad.data.jsonl import read_jsonl
from rag_cad.data.similarity import near_duplicates_against, normalise
from rag_cad.evaluation.detector_metrics import THRESHOLD, summarise

ADAPTED_TRAIN = "adapted/cad_original_train.jsonl"
ADAPTED_TEST = "adapted/cad_original_test.jsonl"
REFERENCE_PREDICTIONS = "reference_checkpoint_test_predictions.jsonl"
HEAD_PREDICTIONS = "test_predictions.jsonl"
EXCLUSIONS = ("full", "minus_verbatim", "minus_near")
HEADLINE = (("masked_average_precision", "upstream_masked", "average_precision"),
            ("masked_tpr", "upstream_masked", "tpr"),
            ("all_rows_average_precision", "all_rows", "average_precision"),
            ("all_rows_tpr", "all_rows", "tpr"))


def malicious_sentences(records: list[dict]) -> list[tuple[tuple[str, int], str]]:
    return [((record["record_id"], sentence["sentence_id"]), sentence["text"])
            for record in records for sentence in record["sentences"] if sentence["label"] == 1]


def leaked_test_records(train: list[dict], test: list[dict], *, near_duplicate_threshold: float) -> dict:
    """Test records whose malicious sentences also occur among the training malicious sentences.

    verbatim: identical after normalisation. near: Jaccard over word shingles at or above the
    threshold (verbatim pairs score 1.0 and are included).
    """
    train_items, test_items = malicious_sentences(train), malicious_sentences(test)
    train_texts = {normalise(text) for _, text in train_items}
    verbatim = {key[0] for key, text in test_items if normalise(text) in train_texts}
    pairs = near_duplicates_against(test_items, train_items, near_duplicate_threshold)
    near = {key[0] for key, _, _ in pairs} | verbatim
    shared = Counter(normalise(text) for key, text in test_items if normalise(text) in train_texts)
    return {"near_duplicate_threshold": near_duplicate_threshold,
            "verbatim_records": sorted(verbatim), "near_records": sorted(near),
            "near_duplicate_pairs": len(pairs),
            "shared_verbatim_sentences": [{"normalised_text": text, "test_occurrences": count}
                                          for text, count in shared.most_common()]}


def prediction_files(artefact: Path) -> dict[str, Path]:
    files = {}
    for path in sorted(artefact.glob(f"models/*/seed_*/{HEAD_PREDICTIONS}")):
        files[f"{path.parents[1].name}/{path.parent.name}"] = path
    reference = artefact / REFERENCE_PREDICTIONS
    if reference.is_file():
        files["released_checkpoint"] = reference
    if not files:
        raise ValueError("No prediction files found in the artefact")
    return files


def _aligned_predictions(files: dict[str, Path]) -> tuple[list[tuple[str, int]], dict[str, list[dict]]]:
    loaded = {name: read_jsonl(path) for name, path in files.items()}
    keys = None
    for name, rows in loaded.items():
        current = [(row["record_id"], row["sentence_id"]) for row in rows]
        if keys is None:
            keys = current
        elif current != keys:
            raise ValueError(f"Prediction rows of {name} do not align with the other heads")
    return keys, loaded


def _mean_std(values: list[float | None]) -> dict:
    present = [value for value in values if value is not None]
    if not present:
        return {"mean": None, "std": None, "n": 0}
    array = np.asarray(present, dtype=float)
    return {"mean": float(array.mean()), "std": float(array.std()), "n": len(present)}


def leak_excluded_report(artefact: Path, *, threshold: float = THRESHOLD,
                         near_duplicate_threshold: float = 0.8) -> dict:
    train = read_jsonl(artefact / ADAPTED_TRAIN)
    test = read_jsonl(artefact / ADAPTED_TEST)
    leaked = leaked_test_records(train, test, near_duplicate_threshold=near_duplicate_threshold)
    files = prediction_files(artefact)
    keys, loaded = _aligned_predictions(files)
    first = next(iter(loaded.values()))
    labels = np.array([row["label"] for row in first], dtype=int)
    mask = np.array([row["upstream_mask"] for row in first], dtype=bool)
    record_ids = np.array([key[0] for key in keys])
    exclusions = {"full": set(), "minus_verbatim": set(leaked["verbatim_records"]),
                  "minus_near": set(leaked["near_records"])}
    heads = {}
    for name, rows in loaded.items():
        scores = np.array([row["probability"] for row in rows], dtype=float)
        heads[name] = {}
        for exclusion, excluded in exclusions.items():
            keep = ~np.isin(record_ids, sorted(excluded))
            heads[name][exclusion] = {
                "rows": int(keep.sum()), "records": int(len(set(record_ids[keep]))),
                "all_rows": summarise(labels[keep], scores[keep], threshold=threshold),
                "upstream_masked": summarise(labels[keep], scores[keep], mask=mask[keep],
                                             threshold=threshold)}
    seed_heads = [name for name in heads if name != "released_checkpoint"]
    aggregate = {}
    for exclusion in EXCLUSIONS:
        aggregate[exclusion] = {}
        for label, block, metric in HEADLINE:
            values = []
            for name in seed_heads:
                section = heads[name][exclusion][block]
                values.append(section[metric] if metric in section
                              else section["at_threshold_strict"][metric])
            aggregate[exclusion][label] = _mean_std(values)
    flagged = [{(row["record_id"], row["sentence_id"]) for row in rows
                if row["label"] == 0 and row["decision"]} for rows in loaded.values()]
    shared_keys = sorted(set.intersection(*flagged))
    by_record = {record["record_id"]: record for record in test}
    probabilities = {name: {(row["record_id"], row["sentence_id"]): row["probability"] for row in rows}
                     for name, rows in loaded.items()}
    shared = []
    for record_id, sentence_id in shared_keys:
        record = by_record[record_id]
        sentence = next(item for item in record["sentences"] if item["sentence_id"] == sentence_id)
        shared.append({"record_id": record_id, "sentence_id": sentence_id,
                       "domain": record.get("domain"), "query": record["query"],
                       "text": sentence["text"],
                       "probabilities": {name: probabilities[name][(record_id, sentence_id)]
                                         for name in loaded}})
    return {"artefact": str(artefact.resolve()), "threshold": threshold,
            "test_records": len(test), "test_rows": int(len(labels)),
            "leaked": leaked, "heads": heads, "seed_aggregate": aggregate,
            "false_positives": {"per_head": {name: len(keys_) for name, keys_ in zip(loaded, flagged)},
                                "shared_count": len(shared), "union_count": len(set.union(*flagged)),
                                "shared_rows": shared,
                                "distinct_shared_texts": sorted({normalise(item["text"])
                                                                 for item in shared})}}
