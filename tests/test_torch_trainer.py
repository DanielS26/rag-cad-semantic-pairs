from pathlib import Path

import numpy as np
import pytest
import yaml

torch = pytest.importorskip("torch")

from rag_cad.cad.upstream_adapter import load_checkpoint  # noqa: E402
from rag_cad.training.recipe import training_recipe  # noqa: E402
from rag_cad.training.torch_trainer import TorchTrainer  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def synthetic(seed: int = 0, rows: int = 192):
    rng = np.random.default_rng(seed)
    features = rng.normal(scale=0.5, size=(rows, 2048)).astype(np.float32)
    labels = (rng.random(rows) < 0.3).astype(np.int64)
    features[labels == 1, :16] += 2.0
    return features, labels


def test_torch_trainer_follows_the_recipe_and_reproduces_itself(tmp_path):
    recipe = training_recipe(yaml.safe_load((ROOT / "configs/experiment.yaml").read_text(encoding="utf-8")))
    features, labels = synthetic()
    trainer = TorchTrainer(recipe, device="cpu")
    first = trainer.fit(features, labels, seed=0)
    history = first["history"]
    assert len(history["epoch_mean_loss"]) == 30 and history["epoch_mean_loss"][-1] < history["epoch_mean_loss"][0]
    negatives, positives = (labels == 0).sum(), (labels == 1).sum()
    expected = np.array([1 / negatives, 1 / positives])
    assert history["class_weights"] == pytest.approx(list(expected / expected.sum()))
    probabilities = trainer.predict(first, features)
    assert probabilities.shape == (192, 2) and np.isfinite(probabilities).all()
    assert probabilities[labels == 1, 1].mean() > probabilities[labels == 0, 1].mean()
    second = trainer.fit(features, labels, seed=0)
    for name, tensor in first["model"].state_dict().items():
        assert torch.equal(tensor, second["model"].state_dict()[name])
    third = trainer.fit(features, labels, seed=1)
    assert not all(torch.equal(tensor, third["model"].state_dict()[name])
                   for name, tensor in first["model"].state_dict().items())
    path = tmp_path / "model.pt"
    metadata = {"hidden": [256, 128], "threshold": 0.5, "condition": "m0_base", "seed": 0,
                "representation_id": "r" * 64, "created_utc": "2026-10-04T00:00:00+00:00"}
    checkpoint_hash = trainer.save(first, path, metadata)
    _, inspection = load_checkpoint(path, checkpoint_hash, with_inspection=True)
    assert inspection["metadata"]["best_threshold"] == 0.5 and inspection["parameter_count"] == 557698
    assert np.allclose(trainer.reload_predict(path, checkpoint_hash, features), probabilities, atol=1e-6)
    with pytest.raises(ValueError, match="hash mismatch"):
        trainer.reload_predict(path, "0" * 64, features)
    with pytest.raises(ValueError, match="2048"):
        trainer.fit(features[:, :10], labels, seed=0)
