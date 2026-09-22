"""Sentence-level detector metrics in NumPy, matching the upstream evaluator's definitions.

Average precision and ROC-AUC follow scikit-learn's step-wise and rank definitions so
that values computed here agree with the pinned upstream train_and_eval.py, which
reports AUPRC, ROC-AUC and TPR/FPR at threshold 0.5 on boundary-masked rows.
"""

import numpy as np

THRESHOLD = 0.5
BOUNDARY_HEAD = 3
BOUNDARY_TAIL = 5


def _validate(labels, scores) -> tuple[np.ndarray, np.ndarray]:
    labels = np.asarray(labels)
    scores = np.asarray(scores, dtype=np.float64)
    if labels.ndim != 1 or labels.shape != scores.shape:
        raise ValueError("Labels and scores must be aligned one-dimensional arrays")
    if not np.isfinite(scores).all() or ((scores < 0) | (scores > 1)).any():
        raise ValueError("Scores must be probabilities in [0, 1]")
    if not np.isin(labels, (0, 1)).all():
        raise ValueError("Labels must be 0 or 1")
    return labels.astype(np.int64), scores


def _average_ranks(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="stable")
    ordered = values[order]
    boundaries = np.flatnonzero(np.diff(ordered)) + 1
    starts = np.r_[0, boundaries]
    ends = np.r_[boundaries, len(values)]
    ranks = np.empty(len(values), dtype=np.float64)
    for start, end in zip(starts, ends):
        ranks[order[start:end]] = (start + 1 + end) / 2
    return ranks


def average_precision(labels, scores) -> float | None:
    """Step-wise area under the precision-recall curve over distinct thresholds."""
    labels, scores = _validate(labels, scores)
    positives = int(labels.sum())
    if positives == 0:
        return None
    if positives == len(labels):
        return 1.0
    order = np.argsort(-scores, kind="stable")
    ordered_scores, ordered_labels = scores[order], labels[order]
    last_of_threshold = np.r_[np.flatnonzero(np.diff(ordered_scores)), len(ordered_scores) - 1]
    true_positives = np.cumsum(ordered_labels)[last_of_threshold]
    false_positives = (last_of_threshold + 1) - true_positives
    precision = true_positives / (true_positives + false_positives)
    recall = true_positives / positives
    return float(np.sum(np.diff(np.r_[0.0, recall]) * precision))


def roc_auc(labels, scores) -> float | None:
    """Rank-based ROC-AUC with average ranks for ties."""
    labels, scores = _validate(labels, scores)
    positives = int(labels.sum())
    negatives = len(labels) - positives
    if positives == 0 or negatives == 0:
        return None
    ranks = _average_ranks(scores)
    return float((ranks[labels == 1].sum() - positives * (positives + 1) / 2) / (positives * negatives))


def confusion(labels, scores, threshold: float = THRESHOLD, *, inclusive: bool = True) -> dict:
    """Counts and rates at one threshold; inclusive mirrors upstream (>=), strict the deployed filter (>)."""
    labels, scores = _validate(labels, scores)
    predicted = scores >= threshold if inclusive else scores > threshold
    tp = int((predicted & (labels == 1)).sum())
    fp = int((predicted & (labels == 0)).sum())
    fn = int((~predicted & (labels == 1)).sum())
    tn = int((~predicted & (labels == 0)).sum())
    tpr = tp / (tp + fn) if tp + fn else None
    fpr = fp / (fp + tn) if fp + tn else None
    precision = tp / (tp + fp) if tp + fp else None
    if precision is None or tpr is None:
        f1 = None
    else:
        f1 = 2 * precision * tpr / (precision + tpr) if precision + tpr else 0.0
    return {"threshold": threshold, "rule": ">=" if inclusive else ">", "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "tpr": tpr, "fpr": fpr, "precision": precision, "recall": tpr, "f1": f1}


def upstream_boundary_mask(units: int, start: int, end: int) -> list[bool]:
    """Upstream train_and_eval.py rule: drop injection rows outside [start+3, end-5]; keep all others."""
    if type(units) is not int or units < 1 or type(start) is not int or type(end) is not int \
            or not 0 <= start <= end < units:
        raise ValueError("Invalid unit count or injection span")
    core_start, core_end = start + BOUNDARY_HEAD, end - BOUNDARY_TAIL
    return [not (start <= index <= end and (index < core_start or index > core_end)) for index in range(units)]


def summarise(labels, scores, *, mask=None, threshold: float = THRESHOLD) -> dict:
    """All metrics for one score vector, optionally restricted to the rows where mask is true."""
    labels, scores = _validate(labels, scores)
    if mask is not None:
        mask = np.asarray(mask, dtype=bool)
        if mask.shape != labels.shape:
            raise ValueError("Mask must align with the rows")
        labels, scores = labels[mask], scores[mask]
    positives = int(labels.sum())
    return {"rows": int(len(labels)), "positives": positives, "negatives": int(len(labels) - positives),
            "average_precision": average_precision(labels, scores) if len(labels) else None,
            "roc_auc": roc_auc(labels, scores) if len(labels) else None,
            "at_threshold_inclusive": confusion(labels, scores, threshold, inclusive=True),
            "at_threshold_strict": confusion(labels, scores, threshold, inclusive=False)}
