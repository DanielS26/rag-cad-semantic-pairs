import re
from copy import deepcopy
from pathlib import Path

import pytest

from rag_cad.data.jsonl import read_jsonl
from rag_cad.data.validate import roundtrip_failures, validate_dataset

FIXTURE = Path(__file__).resolve().parents[1] / "tests/fixtures/phase2_families.jsonl"


def fake_tokenize(text):
    """Deterministic CPU stand-in for the frozen NLTK segmenter used in the tested profile."""
    return [part for part in re.split(r"(?<=[.!?])\s+", text.strip()) if part]


def test_every_fixture_record_survives_join_and_resegment():
    records = read_jsonl(FIXTURE)
    assert roundtrip_failures(records, fake_tokenize) == []
    assert validate_dataset(records, tokenize=fake_tokenize)["roundtrip"] == "passed"
    assert validate_dataset(records)["roundtrip"] == "not_checked"


def test_a_unit_holding_two_sentences_fails_the_round_trip():
    records = read_jsonl(FIXTURE)
    broken = deepcopy(records)
    broken[0]["sentences"][0]["text"] = "First part of the unit. Second part of the same unit."
    assert roundtrip_failures(broken, fake_tokenize) == [broken[0]["record_id"]]
    with pytest.raises(ValueError, match="round trip failed for 1 records"):
        validate_dataset(broken, tokenize=fake_tokenize)
