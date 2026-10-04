"""The real trainer: the fixed CAD head trained with the pinned upstream recipe in torch.

torch is imported only when a trainer is constructed, never at module import, so the CPU
command surface stays importable without it.
"""

from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from rag_cad.operations.provenance import sha256
from rag_cad.training.recipe import class_weights


class TorchTrainer:
    kind = "torch"
    checkpoint_file = "model.pt"

    def __init__(self, recipe: dict, *, device: str | None = None):
        import torch

        self.torch = torch
        self.recipe = recipe
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

    def fit(self, features, labels, *, seed: int) -> dict:
        """AdamW, cosine annealing, class-balanced cross-entropy, shuffled mini-batches, fixed seed."""
        torch = self.torch
        from rag_cad.cad.upstream_adapter import classifier

        recipe = self.recipe
        torch.manual_seed(seed)
        torch.use_deterministic_algorithms(True, warn_only=True)
        torch.backends.cudnn.benchmark = False
        values = torch.from_numpy(np.ascontiguousarray(features, dtype=np.float32))
        targets = torch.from_numpy(np.asarray(labels, dtype=np.int64))
        if values.ndim != 2 or values.shape[1] != recipe["architecture"]["input_dim"] or len(values) != len(targets):
            raise ValueError("Training features must be [N, 2048] with one label per row")
        weights = torch.tensor(class_weights(targets.numpy()), dtype=torch.float32, device=self.device)
        model = classifier().to(self.device)
        model.train()
        optimizer = torch.optim.AdamW(model.parameters(), lr=recipe["learning_rate"],
                                      weight_decay=recipe["weight_decay"])
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=recipe["epochs"])
        generator = torch.Generator().manual_seed(seed)
        loader = torch.utils.data.DataLoader(torch.utils.data.TensorDataset(values, targets),
                                             batch_size=recipe["batch_size"], shuffle=True,
                                             generator=generator, num_workers=0)
        losses = []
        started = datetime.now(timezone.utc)
        for _ in range(recipe["epochs"]):
            total, batches = 0.0, 0
            for batch_values, batch_targets in loader:
                batch_values = batch_values.to(self.device)
                batch_targets = batch_targets.to(self.device)
                optimizer.zero_grad(set_to_none=True)
                loss = torch.nn.functional.cross_entropy(model(batch_values), batch_targets, weight=weights)
                loss.backward()
                optimizer.step()
                total += float(loss.item())
                batches += 1
            scheduler.step()
            losses.append(total / max(batches, 1))
        model.eval()
        history = {"epoch_mean_loss": losses, "class_weights": weights.tolist(), "rows": int(len(targets)),
                   "positives": int(targets.sum()), "device": self.device,
                   "started_utc": started.isoformat(timespec="seconds"),
                   "finished_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        return {"model": model, "seed": seed, "history": history}

    def predict(self, trained: dict, features, *, batch_size: int = 4096) -> np.ndarray:
        torch = self.torch
        model = trained["model"]
        model.eval()
        chunks = []
        with torch.no_grad():
            for start in range(0, len(features), batch_size):
                batch = torch.from_numpy(np.ascontiguousarray(features[start:start + batch_size],
                                                              dtype=np.float32)).to(self.device)
                chunks.append(torch.softmax(model(batch), dim=-1).cpu().numpy())
        return np.concatenate(chunks).astype(np.float32)

    def save(self, trained: dict, path: Path, metadata: dict) -> str:
        """model.pt with the upstream-compatible metadata plus the handoff Section 7.3 fields."""
        torch = self.torch
        state = {name: tensor.detach().cpu() for name, tensor in trained["model"].state_dict().items()}
        torch.save({"model_state_dict": state, "input_dim": 2048, "d_hid": 256, "dropout": 0.3,
                    "best_threshold": 0.5, **metadata}, path)
        return sha256(path)

    def reload_predict(self, path: Path, expected_hash: str, features) -> np.ndarray:
        torch = self.torch
        from rag_cad.cad.upstream_adapter import load_checkpoint

        model, _ = load_checkpoint(path, expected_hash, with_inspection=True)
        with torch.no_grad():
            return torch.softmax(model(torch.from_numpy(np.ascontiguousarray(features, dtype=np.float32))),
                                 dim=-1).numpy().astype(np.float32)
