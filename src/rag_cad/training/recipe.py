"""The fixed training recipe: validated from configs/experiment.yaml, never defaulted.

The architecture is the released CAD head (2048 -> 256 -> 128 -> 2 with dropout 0.3) and the
optimisation recipe is the one the pinned detector/train_and_eval.py implements: AdamW at
1e-3 with weight decay 1e-4, cosine annealing over the epochs, batch size 64, inverse-frequency
class-balanced cross-entropy, and the final epoch as the primary checkpoint.
"""

import math

import numpy as np

ARCHITECTURE = {"input_dim": 2048, "hidden": [256, 128], "output_dim": 2, "dropout": 0.3}
OPTIMIZER = "AdamW"
SCHEDULE = "cosine"
LOSS = "inverse_frequency_class_balanced_cross_entropy"
THRESHOLD = 0.5
FIELDS = ("seeds", "epochs", "batch_size", "optimizer", "learning_rate", "weight_decay",
          "schedule", "loss", "primary_checkpoint_epoch")


def _positive_int(value) -> bool:
    return not isinstance(value, bool) and type(value) is int and value > 0


def training_recipe(experiment: dict) -> dict:
    """Return the resolved recipe or refuse: architecture and recipe are the contract, not options."""
    if experiment.get("architecture") != ARCHITECTURE:
        raise ValueError("Experiment architecture differs from the fixed CAD head")
    if experiment.get("threshold") != THRESHOLD:
        raise ValueError("Experiment threshold differs from the contract value")
    training = experiment.get("training")
    if not isinstance(training, dict) or set(training) != set(FIELDS):
        raise ValueError("Experiment training block must hold exactly the recipe fields")
    seeds = training["seeds"]
    if (not isinstance(seeds, list) or not seeds or len(set(seeds)) != len(seeds)
            or any(isinstance(seed, bool) or type(seed) is not int or seed < 0 for seed in seeds)):
        raise ValueError("Training seeds must be distinct non-negative integers")
    for key in ("epochs", "batch_size", "primary_checkpoint_epoch"):
        if not _positive_int(training[key]):
            raise ValueError(f"Training {key} must be a positive integer")
    for key in ("learning_rate", "weight_decay"):
        value = training[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError(f"Training {key} must be a finite non-negative number")
    if training["learning_rate"] <= 0:
        raise ValueError("Training learning_rate must be positive")
    if training["optimizer"] != OPTIMIZER or training["schedule"] != SCHEDULE or training["loss"] != LOSS:
        raise ValueError("Training optimizer, schedule or loss differs from the recipe")
    if training["primary_checkpoint_epoch"] != training["epochs"]:
        raise ValueError("The primary checkpoint is the final epoch; the recipe has no early stopping")
    return {**training, "seeds": list(seeds), "architecture": dict(ARCHITECTURE), "threshold": THRESHOLD}


def class_weights(labels) -> list[float]:
    """Inverse-frequency class weights normalised to sum to one, as the upstream trainer computes them."""
    values = np.asarray(labels)
    if values.ndim != 1 or values.size == 0 or not np.isin(values, (0, 1)).all():
        raise ValueError("Training labels must be a non-empty vector of 0 and 1")
    counts = np.bincount(values.astype(np.int64), minlength=2)
    if (counts == 0).any():
        raise ValueError("Training labels must contain both classes")
    weights = 1.0 / counts.astype(np.float64)
    weights /= weights.sum()
    return [float(weight) for weight in weights]
