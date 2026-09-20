from copy import deepcopy

import pytest

from rag_cad.data.cad_release_adapter import adapt_record, parse_segments


def record():
    return {"user": "Synthetic query", "sentence_segments": "[0] First.\n[1] Target.",
            "injection_span_unit": {"start": 1, "end": 1}}


def test_explicit_labels_and_missing_count():
    adapted = adapt_record(record(), "original_train")
    assert adapted["labels"] == [0, 1]
    assert adapted["provenance"]["supplied_total_units"] is None


def test_original_counts_fail_but_paraphrase_counts_are_logged():
    source = record() | {"total_units": 9, "source_file": "agentdojo_slack_scenarios/slack_scenario_0/x.json"}
    before = deepcopy(source)
    with pytest.raises(ValueError, match="mismatch"):
        adapt_record(source, "original_train")
    adapted = adapt_record(source, "paraphrased_train")
    assert adapted["provenance"]["total_units_mismatch"]
    assert adapted["provenance"]["normalized_source_file"] == "slack_scenario_0/x.json"
    assert source == before


@pytest.mark.parametrize("raw", ["[1] Missing zero", "[0] A\n[0] Duplicate", "[0]", [], [None]])
def test_malformed_segments_fail(raw):
    with pytest.raises(ValueError):
        parse_segments(raw)


@pytest.mark.parametrize("span", [{"start": -1, "end": 1}, {"start": 1, "end": 3}, {"start": True, "end": 1}])
def test_bad_spans_fail(span):
    with pytest.raises(ValueError, match="span"):
        adapt_record(record() | {"injection_span_unit": span}, "original_test")