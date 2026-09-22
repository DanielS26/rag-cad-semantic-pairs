import numpy as np
import pytest

from rag_cad.evaluation.detector_metrics import (
    average_precision,
    confusion,
    roc_auc,
    summarise,
    upstream_boundary_mask,
)


def test_average_precision_and_roc_auc_match_reference_values():
    labels, scores = [0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8]
    assert average_precision(labels, scores) == pytest.approx(0.8333333333)
    assert roc_auc(labels, scores) == pytest.approx(0.75)
    assert average_precision([1, 0, 1, 0], [0.9, 0.8, 0.7, 0.1]) == pytest.approx(0.8333333333)
    assert roc_auc([1, 0, 1, 0], [0.9, 0.8, 0.7, 0.1]) == pytest.approx(0.75)
    assert average_precision([1, 1, 0, 0], [0.9, 0.8, 0.7, 0.1]) == 1.0 and roc_auc([1, 1, 0, 0], [0.9, 0.8, 0.7, 0.1]) == 1.0
    assert average_precision([0, 0, 1, 1], [0.9, 0.8, 0.7, 0.1]) == pytest.approx(0.4166666667)


def test_ties_and_degenerate_inputs():
    assert roc_auc([1, 0], [0.5, 0.5]) == 0.5
    assert average_precision([1, 0], [0.5, 0.5]) == 0.5
    assert roc_auc([1, 0, 1, 0], [0.7, 0.7, 0.2, 0.2]) == 0.5
    assert average_precision([0, 0], [0.1, 0.2]) is None and roc_auc([0, 0], [0.1, 0.2]) is None
    assert average_precision([1, 1], [0.1, 0.2]) == 1.0 and roc_auc([1, 1], [0.1, 0.2]) is None
    with pytest.raises(ValueError, match="probabilities"):
        average_precision([1, 0], [1.5, 0.2])
    with pytest.raises(ValueError, match="0 or 1"):
        roc_auc([2, 0], [0.5, 0.2])
    with pytest.raises(ValueError, match="aligned"):
        confusion([1, 0, 1], [0.5, 0.2])


def test_confusion_inclusive_versus_strict_at_the_threshold():
    labels, scores = [1, 1, 0, 0], [0.5, 0.9, 0.5, 0.1]
    inclusive = confusion(labels, scores)
    strict = confusion(labels, scores, inclusive=False)
    assert (inclusive["tp"], inclusive["fp"], inclusive["fn"], inclusive["tn"]) == (2, 1, 0, 1)
    assert (strict["tp"], strict["fp"], strict["fn"], strict["tn"]) == (1, 0, 1, 2)
    assert inclusive["tpr"] == 1.0 and inclusive["fpr"] == 0.5 and inclusive["rule"] == ">="
    assert strict["precision"] == 1.0 and strict["recall"] == 0.5 and strict["f1"] == pytest.approx(2 / 3)
    empty = confusion([0, 0], [0.1, 0.2])
    assert empty["tpr"] is None and empty["precision"] is None and empty["f1"] is None and empty["fpr"] == 0.0


def test_upstream_boundary_mask_matches_the_pinned_rule():
    mask = upstream_boundary_mask(20, 0, 15)
    assert mask[:3] == [False] * 3 and mask[3:11] == [True] * 8 and mask[11:16] == [False] * 5
    assert mask[16:] == [True] * 4
    assert upstream_boundary_mask(12, 2, 9) == [True, True] + [False] * 8 + [True, True]
    assert upstream_boundary_mask(1, 0, 0) == [False]
    for units, start, end in ((0, 0, 0), (5, 3, 2), (5, -1, 2), (5, 0, 5)):
        with pytest.raises(ValueError):
            upstream_boundary_mask(units, start, end)


def test_summarise_applies_mask_and_reports_both_rules():
    labels = np.array([1, 1, 1, 0, 0, 0])
    scores = np.array([0.9, 0.5, 0.2, 0.6, 0.5, 0.1])
    full = summarise(labels, scores)
    assert full["rows"] == 6 and full["positives"] == 3
    assert full["at_threshold_inclusive"]["tp"] == 2 and full["at_threshold_strict"]["tp"] == 1
    masked = summarise(labels, scores, mask=[True, False, True, True, False, True])
    assert masked["rows"] == 4 and masked["positives"] == 2
    assert masked["roc_auc"] == pytest.approx(0.75)
    with pytest.raises(ValueError, match="align"):
        summarise(labels, scores, mask=[True])
    assert summarise([], [])["average_precision"] is None
