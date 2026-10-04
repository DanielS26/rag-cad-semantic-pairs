from pathlib import Path

import numpy as np
import pytest
import yaml

from rag_cad.data.split import assign_splits, pinned_split
from rag_cad.evaluation.offline import aggregate, boundary_mask, evaluate_rows, prediction_rows
from rag_cad.training.fake_trainer import FakeTrainer
from rag_cad.training.recipe import class_weights, training_recipe

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = yaml.safe_load((ROOT / "configs/experiment.yaml").read_text(encoding="utf-8"))


def test_recipe_accepts_the_experiment_config_and_refuses_changes():
    recipe = training_recipe(EXPERIMENT)
    assert recipe["seeds"] == [0, 1, 2] and recipe["epochs"] == 30 and recipe["batch_size"] == 64
    assert recipe["architecture"]["hidden"] == [256, 128] and recipe["threshold"] == 0.5
    assert recipe["optimizer"] == "AdamW" and recipe["learning_rate"] == 0.001 and recipe["weight_decay"] == 0.0001
    training = EXPERIMENT["training"]
    for bad in ({"architecture": {**EXPERIMENT["architecture"], "dropout": 0.5}}, {"threshold": 0.4},
                {"training": {**training, "optimizer": "SGD"}}, {"training": {**training, "seeds": [0, 0]}},
                {"training": {**training, "primary_checkpoint_epoch": 10}},
                {"training": {**training, "learning_rate": 0}},
                {"training": {key: value for key, value in training.items() if key != "loss"}}):
        with pytest.raises(ValueError):
            training_recipe(EXPERIMENT | bad)


def test_class_weights_follow_the_upstream_formula():
    assert class_weights([0, 0, 0, 1]) == pytest.approx([0.25, 0.75])
    for bad in ([0, 0], [], [0, 2]):
        with pytest.raises(ValueError):
            class_weights(bad)


def rows_for(record_lengths: dict) -> list[dict]:
    return [{"record_id": record, "sentence_id": sentence,
             "condition_source": "test_only" if record.startswith("t") else "base"}
            for record, length in record_lengths.items() for sentence in range(length)]


def test_boundary_mask_offline_metrics_predictions_and_aggregate():
    rows = rows_for({"a": 12, "t": 4})
    labels = np.array([0, 0] + [1] * 8 + [0, 0] + [0, 1, 0, 0])
    mask, non_contiguous = boundary_mask(rows, labels)
    assert mask.tolist() == [True, True] + [False] * 8 + [True, True] + [True, False, True, True]
    assert non_contiguous == 0
    probabilities = np.column_stack([1 - labels * 0.8 - 0.1, labels * 0.8 + 0.1])
    report = evaluate_rows(labels, probabilities, rows)
    assert report["rows"] == 16 and report["positives"] == 9 and report["masked_out_rows"] == 9
    assert report["all_rows"]["roc_auc"] == 1.0 and report["upstream_masked"]["positives"] == 0
    assert set(report["by_condition_source_masked"]) == {"base", "test_only"}
    predictions = prediction_rows(rows, labels, probabilities)
    assert len(predictions) == 16 and predictions[2]["decision"] is True and predictions[2]["upstream_mask"] is False
    assert predictions[0] == {"record_id": "a", "sentence_id": 0, "label": 0, "probability": pytest.approx(0.1),
                              "decision": False, "upstream_mask": True}
    _, non_contiguous = boundary_mask(rows_for({"b": 5}), np.array([1, 0, 1, 0, 0]))
    assert non_contiguous == 1
    summary = aggregate({"0": report, "1": report})
    assert summary["all_rows_roc_auc"] == {"mean": 1.0, "std": 0.0, "seeds": 2}
    assert summary["masked_average_precision"] is None
    with pytest.raises(ValueError, match="align"):
        evaluate_rows(labels[:-1], probabilities, rows)


def test_fake_trainer_is_deterministic_and_verifies_its_checkpoint(tmp_path):
    recipe = training_recipe(EXPERIMENT)
    rng = np.random.default_rng(0)
    features = rng.normal(size=(40, 2048)).astype(np.float32)
    labels = np.array([0] * 30 + [1] * 10)
    features[labels == 1, :8] += 3.0
    trainer = FakeTrainer(recipe)
    first = trainer.fit(features, labels, seed=0)
    second = trainer.fit(features, labels, seed=0)
    assert first["model"] == second["model"] and first["history"]["class_weights"] == pytest.approx([0.25, 0.75])
    assert len(first["history"]["epoch_mean_loss"]) == 30
    probabilities = trainer.predict(first, features)
    assert probabilities.shape == (40, 2) and np.allclose(probabilities.sum(axis=1), 1)
    assert probabilities[labels == 1, 1].mean() > probabilities[labels == 0, 1].mean()
    assert not np.allclose(trainer.predict(trainer.fit(features, labels, seed=1), features), probabilities)
    path = tmp_path / "model.json"
    checkpoint_hash = trainer.save(first, path, {"condition": "m0_base", "seed": 0})
    assert np.allclose(trainer.reload_predict(path, checkpoint_hash, features), probabilities)
    with pytest.raises(ValueError, match="hash mismatch"):
        trainer.reload_predict(path, "0" * 64, features)


def record(record_id: str, source: str, condition_source: str, group: str, text: str) -> dict:
    return {"record_id": record_id, "group_id": group, "family_id": None, "split": None,
            "condition_source": condition_source, "query": "Synthetic query.", "domain": "banking",
            "attack_goal": "agentdojo_injection", "pair_member": "unpaired",
            "sentences": [{"sentence_id": 0, "text": f"Benign {text}.", "label": 0, "semantic_role": None,
                           "is_target": False},
                          {"sentence_id": 1, "text": f"Injected {text}.", "label": 1,
                           "semantic_role": "injected_instruction", "is_target": True}],
            "provenance": {"source_dataset": source, "source_record_id": record_id, "generator_model": None,
                           "generator_prompt_hash": None, "licence": "CC-BY-4.0", "review_status": "unreviewed"}}


def test_d0_records_pin_to_train_and_released_test_records_to_test():
    d0 = record("cad_original_train:x", "cad_original_train", "base", "cad_scenario:banking_scenario_0", "one")
    test = record("cad_original_test:y", "cad_original_test", "test_only", "cad_original_test:banking/user_task_0", "two")
    para = record("cad_paraphrased_train:z", "cad_paraphrased_train", "base", "cad_scenario:banking_scenario_0", "three")
    assert pinned_split(d0) == "train" and pinned_split(test) == "test" and pinned_split(para) == "train"
    ratios = {"train": 0.7, "validation": 0.15, "test": 0.15}
    manifest = assign_splits([d0, test, para], ratios, 764)
    assert manifest["assignments"] == {"cad_original_test:banking/user_task_0": "test",
                                       "cad_scenario:banking_scenario_0": "train"}
    assert manifest["d0_holdout_policy"] == "none"
    with pytest.raises(ValueError, match="holdout"):
        assign_splits([d0, test], ratios, 764, d0_holdout_policy="scenario")
