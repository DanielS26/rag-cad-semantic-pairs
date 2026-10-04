"""Offline evaluation of a head over an assembled feature set: all rows, upstream-masked rows,
and the masked rows per condition source."""

import numpy as np

from rag_cad.evaluation.detector_metrics import THRESHOLD, summarise, upstream_boundary_mask


def boundary_mask(rows: list[dict], labels) -> tuple[np.ndarray, int]:
    """The upstream boundary mask derived from each record's labels.

    The malicious rows of a record are taken as one span from the first to the last malicious
    unit (the released data has exactly one contiguous span per record); the first three and
    last five units of that span are dropped. Records without malicious rows keep every row.
    Returns the mask and the number of records whose malicious rows were not contiguous.
    """
    labels = np.asarray(labels)
    mask = np.ones(len(rows), dtype=bool)
    by_record: dict[str, list[int]] = {}
    for index, row in enumerate(rows):
        by_record.setdefault(row["record_id"], []).append(index)
    non_contiguous = 0
    for indices in by_record.values():
        ordered = sorted(indices, key=lambda position: rows[position]["sentence_id"])
        record_labels = [int(labels[position]) for position in ordered]
        positives = [unit for unit, label in enumerate(record_labels) if label == 1]
        if not positives:
            continue
        start, end = positives[0], positives[-1]
        if len(positives) != end - start + 1:
            non_contiguous += 1
        record_mask = upstream_boundary_mask(len(ordered), start, end)
        for unit, position in enumerate(ordered):
            mask[position] = record_mask[unit]
    return mask, non_contiguous


def evaluate_rows(labels, probabilities, rows: list[dict], *, threshold: float = THRESHOLD) -> dict:
    labels = np.asarray(labels)
    scores = np.asarray(probabilities)[:, 1]
    if scores.shape != labels.shape or len(rows) != len(labels):
        raise ValueError("Labels, probabilities and rows must align one to one")
    mask, non_contiguous = boundary_mask(rows, labels)
    sources = np.array([row["condition_source"] for row in rows])
    return {"rows": int(len(rows)), "positives": int(labels.sum()),
            "masked_out_rows": int((~mask).sum()), "non_contiguous_span_records": non_contiguous,
            "all_rows": summarise(labels, scores, threshold=threshold),
            "upstream_masked": summarise(labels, scores, mask=mask, threshold=threshold),
            "by_condition_source_masked": {source: summarise(labels, scores, mask=mask & (sources == source),
                                                             threshold=threshold)
                                           for source in sorted(set(sources))}}


def prediction_rows(rows: list[dict], labels, probabilities, *, threshold: float = THRESHOLD) -> list[dict]:
    labels = np.asarray(labels)
    scores = np.asarray(probabilities)[:, 1]
    mask, _ = boundary_mask(rows, labels)
    return [{"record_id": row["record_id"], "sentence_id": row["sentence_id"], "label": int(labels[index]),
             "probability": float(scores[index]), "decision": bool(scores[index] > threshold),
             "upstream_mask": bool(mask[index])} for index, row in enumerate(rows)]


def aggregate(evaluations: dict[str, dict]) -> dict:
    """Mean and population standard deviation over seeds for the headline metrics."""
    paths = {"masked_average_precision": ("upstream_masked", "average_precision"),
             "masked_roc_auc": ("upstream_masked", "roc_auc"),
             "masked_tpr": ("upstream_masked", "at_threshold_strict", "tpr"),
             "masked_fpr": ("upstream_masked", "at_threshold_strict", "fpr"),
             "all_rows_average_precision": ("all_rows", "average_precision"),
             "all_rows_roc_auc": ("all_rows", "roc_auc")}
    result = {}
    for name, path in paths.items():
        values = []
        for evaluation in evaluations.values():
            value = evaluation
            for key in path:
                value = value[key]
            if value is not None:
                values.append(float(value))
        result[name] = ({"mean": float(np.mean(values)), "std": float(np.std(values)), "seeds": len(values)}
                        if values else None)
    return result
