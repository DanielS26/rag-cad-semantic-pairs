import json
from pathlib import Path

import numpy as np
import pytest

from rag_cad.cad.fake_encoder import FAKE_REPRESENTATION, FakeEncoder
from rag_cad.cad.feature_builder import (
    FeatureBuilder,
    build_condition,
    plan_pools,
    verify_condition,
)
from rag_cad.cad.feature_store import (
    ROW_FIELDS,
    check_alignment,
    read_feature_set,
    write_feature_set,
)
from rag_cad.data.jsonl import read_jsonl
from rag_cad.data.split import assign_splits

FIXTURE = Path(__file__).resolve().parents[1] / "tests/fixtures/phase2_families.jsonl"
RATIOS = {"train": 0.6, "validation": 0.2, "test": 0.2}


def records():
    return read_jsonl(FIXTURE)


def manifest():
    return assign_splits(records(), RATIOS, 764)


def builder(environment="fake-env"):
    return FeatureBuilder(FAKE_REPRESENTATION, FakeEncoder(), feature_environment_id=environment,
                          commit="f" * 40, config_sha256="0" * 64)


def test_assembled_condition_rows_align_with_tensors_and_metadata(tmp_path):
    split = manifest()
    assembled = build_condition(builder(), records(), split, "m3_semantic", "train", tmp_path / "features")
    features, labels, rows, read = read_feature_set(tmp_path / "features/assembled/m3_semantic/train")
    assert features.shape == (36, 2048) and labels.shape == (36,) and len(rows) == 36
    assert features.dtype == np.float32 and labels.dtype == np.int64
    assert read["row_digest"] == assembled["row_digest"] and read["kind"] == "assembled"
    assert [row["feature_row_index"] for row in rows] == list(range(36))
    assert all(tuple(row) == ROW_FIELDS for row in rows)
    assert {row["condition"] for row in rows} == {"m3_semantic"} and {row["split"] for row in rows} == {"train"}
    assert {row["condition_source"] for row in rows} == {"shared_malicious", "semantic_benign"}
    assert {row["representation_id"] for row in rows} == {FAKE_REPRESENTATION.representation_id}
    assert all(int(labels[index]) == row["label"] for index, row in enumerate(rows))
    assert sum(row["is_target"] for row in rows) == 12 and int(labels.sum()) == 6
    assert read["counts"] == {"rows": 36, "records": 12, "malicious_rows": 6, "benign_rows": 30,
                              "target_rows": 12, "families": 6, "groups": 6}
    assert verify_condition(tmp_path / "features", "m3_semantic", "train")["parents"] == sorted(read["parents"])


def test_shared_pools_are_reused_not_re_encoded_across_conditions(tmp_path):
    split = manifest()
    root = tmp_path / "features"
    m3 = build_condition(builder(), records(), split, "m3_semantic", "train", root)
    with pytest.raises(FileExistsError, match="resume"):
        build_condition(builder(), records(), split, "m1_random", "train", root)
    m1 = build_condition(builder(), records(), split, "m1_random", "train", root, resume=True)
    shared = set(m1["parents"]) & set(m3["parents"])
    assert len(shared) == 1
    features_m1, _, rows_m1, _ = read_feature_set(root / "assembled/m1_random/train")
    features_m3, _, rows_m3, _ = read_feature_set(root / "assembled/m3_semantic/train")
    common_m1 = {(row["record_id"], row["sentence_id"]): features_m1[index] for index, row in enumerate(rows_m1)
                 if row["condition_source"] == "shared_malicious"}
    common_m3 = {(row["record_id"], row["sentence_id"]): features_m3[index] for index, row in enumerate(rows_m3)
                 if row["condition_source"] == "shared_malicious"}
    assert common_m1.keys() == common_m3.keys() and len(common_m1) == 18
    for key in common_m1:
        np.testing.assert_array_equal(common_m1[key], common_m3[key])
    assert sorted(shard.name for shard in (root / "shards").iterdir()) == ["random_benign", "semantic_benign",
                                                                            "shared_malicious"]


def test_shard_size_does_not_change_the_assembled_set(tmp_path):
    split = manifest()
    small = build_condition(builder(), records(), split, "m2_keyword", "train", tmp_path / "small",
                            shard_records=1)
    large = build_condition(builder(), records(), split, "m2_keyword", "train", tmp_path / "large")
    assert len(small["parents"]) == 12 and len(large["parents"]) == 2
    assert small["row_digest"] == large["row_digest"] and small["counts"] == large["counts"]
    features_small, _, rows_small, _ = read_feature_set(tmp_path / "small/assembled/m2_keyword/train")
    features_large, _, rows_large, _ = read_feature_set(tmp_path / "large/assembled/m2_keyword/train")
    np.testing.assert_array_equal(features_small, features_large)
    assert rows_small == rows_large


def test_common_validation_and_test_sets(tmp_path):
    split = manifest()
    pools = plan_pools(records(), split)
    assert set(pools) == {"shared_malicious", "random_benign", "keyword_benign", "semantic_benign",
                          "common_validation", "common_test"}
    validation = build_condition(builder(), records(), split, "common", "validation", tmp_path / "f")
    test = build_condition(builder(), records(), split, "common", "test", tmp_path / "f")
    assert validation["counts"]["rows"] == 24 and test["counts"]["rows"] == 24
    _, _, rows, _ = read_feature_set(tmp_path / "f/assembled/common/test")
    assert {row["split"] for row in rows} == {"test"}
    assert {row["condition_source"] for row in rows} == {"shared_malicious", "semantic_benign",
                                                          "keyword_benign", "random_benign"}
    with pytest.raises(ValueError, match="condition common"):
        build_condition(builder(), records(), split, "m3_semantic", "test", tmp_path / "g")
    with pytest.raises(ValueError, match="Unknown condition"):
        build_condition(builder(), records(), split, "common", "train", tmp_path / "g")


def test_tampering_and_identity_drift_are_refused(tmp_path):
    split = manifest()
    root = tmp_path / "features"
    build_condition(builder(), records(), split, "m3_semantic", "train", root)
    with pytest.raises(ValueError, match="identity"):
        build_condition(builder("other-env"), records(), split, "m3_semantic", "train", root, resume=True)
    shard = next((root / "shards/shared_malicious").iterdir())
    rows_path = shard / "rows.jsonl"
    original = rows_path.read_bytes()
    rows_path.write_bytes(original.replace(b'"label":1', b'"label":0', 1))
    with pytest.raises(ValueError, match="hash mismatch"):
        read_feature_set(shard)
    with pytest.raises(ValueError, match="hash mismatch"):
        build_condition(builder(), records(), split, "m3_semantic", "train", root, resume=True)
    rows_path.write_bytes(original)
    manifest_path = shard / "manifest.json"
    edited = json.loads(manifest_path.read_text(encoding="utf-8"))
    edited["counts"]["rows"] += 1
    manifest_path.write_text(json.dumps(edited), encoding="utf-8")
    with pytest.raises(ValueError, match="differ from the manifest"):
        read_feature_set(shard)


def test_write_feature_set_refuses_misalignment(tmp_path):
    from rag_cad.data.split import apply_manifest

    assigned = apply_manifest(records(), manifest())[:2]
    features, labels, rows = builder().build_rows(assigned, condition="probe")
    check_alignment(features, labels, rows)
    identity = builder().identity
    with pytest.raises(ValueError, match="misaligned"):
        write_feature_set(tmp_path / "a", features[:-1], labels[:-1], rows, identity, kind="shard", name="x")
    with pytest.raises(ValueError, match="disagree"):
        write_feature_set(tmp_path / "b", features, 1 - labels, rows, identity, kind="shard", name="x")
    with pytest.raises(ValueError, match="sequential"):
        write_feature_set(tmp_path / "c", features, labels, rows[::-1], identity, kind="shard", name="x")
    with pytest.raises(ValueError, match="finite float32"):
        write_feature_set(tmp_path / "d", features.astype(np.float64), labels, rows, identity, kind="shard", name="x")
    with pytest.raises(ValueError, match="identity"):
        write_feature_set(tmp_path / "e", features, labels, rows, identity | {"commit": ""}, kind="shard", name="x")
    write_feature_set(tmp_path / "ok", features, labels, rows, identity, kind="shard", name="x")
    with pytest.raises(FileExistsError):
        write_feature_set(tmp_path / "ok", features, labels, rows, identity, kind="shard", name="x")
    with pytest.raises(ValueError, match="split must be assigned"):
        builder().encode_record(read_jsonl(FIXTURE)[0], condition="probe")
