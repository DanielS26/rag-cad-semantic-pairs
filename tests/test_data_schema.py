import json
from collections import Counter
from copy import deepcopy
from pathlib import Path

import jsonschema
import pytest

from rag_cad.data.jsonl import load_records, read_jsonl, write_jsonl
from rag_cad.data.schema import ScorerRecord, record_content_hash, validate_record

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/phase2_families.jsonl"
SCHEMA = json.loads((ROOT / "datasets/schemas/scorer_record.schema.json").read_text(encoding="utf-8"))


def fixture():
    return read_jsonl(FIXTURE)


def one(record_id):
    return next(record for record in fixture() if record["record_id"] == record_id)


def mutate(record, path, value):
    changed = deepcopy(record)
    target = changed
    for step in path[:-1]:
        target = target[step]
    target[path[-1]] = value
    return changed


def test_fixture_holds_ten_complete_hand_written_families():
    records, inventory = load_records(FIXTURE)
    assert inventory["records"] == 40 and set(inventory["files"]) == {FIXTURE.name}
    assert len({record["family_id"] for record in records if record["family_id"]}) == 10
    assert len({record["group_id"] for record in records}) == 10
    assert Counter(record["condition_source"] for record in records) == {
        "shared_malicious": 10, "semantic_benign": 10, "keyword_benign": 10, "random_benign": 10}
    assert all(record["split"] is None for record in records)
    assert all(record["provenance"]["review_status"] == "unreviewed" for record in records)


def test_fixture_matches_the_published_json_schema():
    jsonschema.Draft202012Validator.check_schema(SCHEMA)
    validator = jsonschema.Draft202012Validator(SCHEMA)
    for record in fixture():
        validator.validate(record)
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(one("quote_0001_malicious") | {"notes": "extra"})
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(mutate(one("quote_0001_malicious"), ("domain",), "Cyber Security"))


def test_dataclass_view_roundtrips_and_requires_assigned_split_by_default():
    record = one("quote_0001_semantic")
    with pytest.raises(ValueError, match="split must be assigned"):
        validate_record(record)
    view = ScorerRecord.from_dict(record, require_split=False)
    assert view.sentences[1].is_target and view.sentences[1].label == 0
    assert view.to_dict() == validate_record(record, require_split=False)
    assert ScorerRecord.from_dict(record | {"split": "train"}).split == "train"


@pytest.mark.parametrize("path, value, message", [
    (("sentences", 1, "label"), 2, "label must be the integer"),
    (("sentences", 1, "label"), True, "label must be the integer"),
    (("sentences", 1, "label"), "1", "label must be the integer"),
    (("sentences", 0, "sentence_id"), 5, "sequential"),
    (("sentences", 1, "is_target"), False, "not marked as a target"),
    (("sentences", 1, "semantic_role"), None, "without a semantic role"),
    (("sentences", 1, "text"), "Two lines\nhere", "single line"),
    (("split",), "holdout", "Unknown split"),
    (("condition_source",), "bonus", "Unknown condition_source"),
    (("pair_member",), "benign", "entirely benign"),
    (("family_id",), None, "paired members"),
    (("domain",), "Cyber Security", "domain"),
    (("attack_goal",), None, "attack_goal"),
    (("query",), "  ", "query"),
    (("provenance", "licence"), "MIT", "Licence"),
    (("provenance", "source_dataset"), "unknown_corpus", "Unknown source dataset"),
    (("provenance", "generator_model"), "synthetic-model", "set together"),
    (("provenance", "review_status"), "approved", "review status"),
])
def test_invalid_records_fail_validation(path, value, message):
    with pytest.raises(ValueError, match=message):
        validate_record(mutate(one("quote_0001_malicious"), path, value), require_split=False)


def test_adapted_target_sources_carry_their_registered_licence():
    """Malicious targets adapted from BIPIA or ASB validate with MIT; a wrong licence fails (D-20261013-29)."""
    malicious = one("quote_0001_malicious")
    for source, source_id in (("bipia_adapted", "bipia:text_attack_train:instruction:0"),
                              ("asb_adapted", "asb:all_attack_tools:17")):
        record = mutate(mutate(mutate(malicious, ("provenance", "source_dataset"), source),
                               ("provenance", "source_record_id"), source_id), ("provenance", "licence"), "MIT")
        assert validate_record(record, require_split=False)["provenance"]["source_dataset"] == source
        with pytest.raises(ValueError, match="Licence"):
            validate_record(mutate(record, ("provenance", "licence"), "CC-BY-4.0"), require_split=False)

def test_structural_and_cross_field_rules():
    malicious, keyword, semantic = one("quote_0001_malicious"), one("quote_0001_keyword"), one("quote_0001_semantic")
    missing = deepcopy(malicious)
    del missing["provenance"]["licence"]
    with pytest.raises(ValueError, match="Provenance fields"):
        validate_record(missing, require_split=False)
    with pytest.raises(ValueError, match="exactly the contract fields"):
        validate_record(malicious | {"notes": "extra"}, require_split=False)
    with pytest.raises(ValueError, match="benign target outside"):
        validate_record(mutate(mutate(keyword, ("sentences", 0, "is_target"), True),
                               ("sentences", 0, "semantic_role"), "quotation"), require_split=False)
    with pytest.raises(ValueError, match="require a target sentence"):
        validate_record(mutate(mutate(semantic, ("sentences", 1, "is_target"), False),
                               ("sentences", 1, "semantic_role"), None), require_split=False)
    poisoned = mutate(mutate(mutate(keyword, ("sentences", 0, "label"), 1), ("sentences", 0, "is_target"), True),
                      ("sentences", 0, "semantic_role"), "unauthorised_directive") | {"attack_goal": "phishing"}
    with pytest.raises(ValueError, match="Control benign records"):
        validate_record(poisoned, require_split=False)
    upstream = mutate(mutate(malicious, ("provenance", "source_dataset"), "cad_original_test"),
                      ("provenance", "licence"), "CC-BY-4.0")
    with pytest.raises(ValueError, match="source_record_id"):
        validate_record(upstream | {"split": "test"})
    upstream["provenance"]["source_record_id"] = "banking_scenario_0/injection_task_1.json"
    assert validate_record(upstream | {"split": "test"})["split"] == "test"
    with pytest.raises(ValueError, match="Released CAD test records"):
        validate_record(upstream | {"split": "train"})
    with pytest.raises(ValueError, match="test_only records belong"):
        validate_record(malicious | {"condition_source": "test_only", "split": "validation"})
    assert validate_record(malicious | {"condition_source": "test_only", "split": "test"})


def test_content_hash_covers_text_and_labels_only():
    record = one("negation_0002_semantic")
    digest = record_content_hash(record)
    assert len(digest) == 64
    assert record_content_hash(mutate(record, ("provenance", "review_status"), "double_reviewed")) == digest
    assert record_content_hash(mutate(record, ("group_id",), "elsewhere")) == digest
    assert record_content_hash(mutate(record, ("sentences", 0, "text"), "Changed.")) != digest
    assert record_content_hash(mutate(record, ("sentences", 1, "label"), 1)) != digest


def test_jsonl_reading_writing_and_duplicate_ids(tmp_path):
    records = fixture()
    first, second = tmp_path / "a" / "one.jsonl", tmp_path / "a" / "two.jsonl"
    write_jsonl(first, records[:4])
    write_jsonl(second, records[4:8])
    loaded, inventory = load_records(tmp_path / "a")
    assert [record["record_id"] for record in loaded] == [record["record_id"] for record in records[:8]]
    assert set(inventory["files"]) == {"one.jsonl", "two.jsonl"}
    with pytest.raises(FileExistsError):
        write_jsonl(first, records[:1])
    write_jsonl(tmp_path / "a" / "three.jsonl", records[:1])
    with pytest.raises(ValueError, match="Duplicate record_id"):
        load_records(tmp_path / "a")
    with pytest.raises(ValueError, match="Secret-like"):
        write_jsonl(tmp_path / "secret.jsonl", [records[0] | {"query": "token ghp_" + "a" * 30}])
    (tmp_path / "blank.jsonl").write_text('{"a": 1}\n\n{"b": 2}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="Blank line"):
        read_jsonl(tmp_path / "blank.jsonl")
    (tmp_path / "list.jsonl").write_text("[1, 2]\n", encoding="utf-8")
    with pytest.raises(ValueError, match="not a JSON object"):
        read_jsonl(tmp_path / "list.jsonl")
    (tmp_path / "empty").mkdir()
    with pytest.raises(ValueError, match="No JSONL"):
        load_records(tmp_path / "empty")
    with pytest.raises(ValueError, match="JSONL file or a directory"):
        load_records(tmp_path / "missing")
