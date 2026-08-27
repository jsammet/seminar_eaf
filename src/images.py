"""Image helpers for module A: 2D slices, an SVM on pixels, and a small CNN.

The slices are 64x64 and there are only a few hundred of them, so everything
here is deliberately tiny and finishes on a CPU laptop. The CNN uses PyTorch if
it is installed and otherwise falls back to scikit-learn's ``MLPClassifier`` on
the same pixels, so the notebook never dead-ends on a missing dependency.
"""
from pathlib import Path

import numpy as np


def repo_root():
    return next(parent for parent in [Path.cwd(), *Path.cwd().parents] if (parent / "src").exists())


def load_slices():
    """Return (images, table-like dict) for module A's 2D slices.

    ``images`` is float32 in [0, 1] with shape (n, 64, 64).
    """
    archive = np.load(repo_root() / "data" / "derived" / "a_slices.npz", allow_pickle=True)
    images = archive["images"].astype(np.float32) / 255.0
    meta = {key: archive[key] for key in archive.files if key != "images"}
    return images, meta


def flatten(images):
    """(n, 64, 64) -> (n, 4096): one row per scan, one column per pixel."""
    return images.reshape(len(images), -1)


def augment_flips(images, labels, groups=None):
    """Left-right mirroring only.

    A horizontally flipped brain is anatomically arguable (the hemispheres are
    near-symmetric). A vertically flipped brain is nonsense — it would put the
    cerebellum on top. This is why augmentation choices are a domain question.
    """
    flipped = images[:, :, ::-1]
    out_images = np.concatenate([images, flipped])
    out_labels = np.concatenate([labels, labels])
    if groups is None:
        return out_images, out_labels
    return out_images, out_labels, np.concatenate([groups, groups])


def torch_available():
    try:
        import torch  # noqa: F401
        return True
    except ImportError:
        return False


class SmallCNN:
    """A deliberately small convolutional network, with a scikit-learn-like API.

    Two convolution blocks and one dense layer: roughly 15k parameters, which is
    already a lot for a few hundred brains. That mismatch is the lesson.
    Training 12 epochs on ~280 images takes well under a minute on CPU.
    """

    def __init__(self, epochs=12, learning_rate=3e-3, channels=8, dropout=0.3, seed=42, verbose=True):
        self.epochs = epochs
        self.learning_rate = learning_rate
        self.channels = channels
        self.dropout = dropout
        self.seed = seed
        self.verbose = verbose
        self.history = {"epoch": [], "train_loss": [], "validation_loss": [], "validation_accuracy": []}
        self.backend = None

    def _build(self):
        import torch
        from torch import nn

        torch.manual_seed(self.seed)
        c = self.channels
        return nn.Sequential(
            nn.Conv2d(1, c, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),      # 64 -> 32
            nn.Conv2d(c, c * 2, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),  # 32 -> 16
            nn.Conv2d(c * 2, c * 2, 3, padding=1), nn.ReLU(), nn.MaxPool2d(4),  # 16 -> 4
            nn.Flatten(),
            nn.Dropout(self.dropout),
            nn.Linear(c * 2 * 4 * 4, 32), nn.ReLU(),
            nn.Linear(32, 2),
        )

    def fit(self, images, labels, validation=None):
        if not torch_available():
            return self._fit_fallback(images, labels, validation)
        import torch
        from torch import nn

        self.backend = "pytorch"
        self.network = self._build()
        device = torch.device("cpu")
        self.network.to(device)

        x = torch.tensor(images, dtype=torch.float32).unsqueeze(1)
        y = torch.tensor(np.asarray(labels), dtype=torch.long)
        weights = torch.tensor([1.0 / max((y == 0).sum().item(), 1), 1.0 / max((y == 1).sum().item(), 1)],
                               dtype=torch.float32)
        weights = weights / weights.sum() * 2
        criterion = nn.CrossEntropyLoss(weight=weights)
        optimiser = torch.optim.Adam(self.network.parameters(), lr=self.learning_rate)

        if validation is not None:
            x_validation = torch.tensor(validation[0], dtype=torch.float32).unsqueeze(1)
            y_validation = torch.tensor(np.asarray(validation[1]), dtype=torch.long)

        batch_size = 32
        for epoch in range(1, self.epochs + 1):
            self.network.train()
            permutation = torch.randperm(len(x))
            running = 0.0
            for start in range(0, len(x), batch_size):
                batch = permutation[start:start + batch_size]
                optimiser.zero_grad()
                loss = criterion(self.network(x[batch]), y[batch])
                loss.backward()
                optimiser.step()
                running += loss.item() * len(batch)
            self.history["epoch"].append(epoch)
            self.history["train_loss"].append(running / len(x))
            if validation is not None:
                self.network.eval()
                with torch.no_grad():
                    logits = self.network(x_validation)
                    self.history["validation_loss"].append(criterion(logits, y_validation).item())
                    accuracy = (logits.argmax(1) == y_validation).float().mean().item()
                    self.history["validation_accuracy"].append(accuracy)
            if self.verbose:
                message = f"  epoch {epoch:2d}/{self.epochs}  train loss {self.history['train_loss'][-1]:.3f}"
                if validation is not None:
                    message += f"   held-out loss {self.history['validation_loss'][-1]:.3f}"
                    message += f"   held-out accuracy {self.history['validation_accuracy'][-1]:.3f}"
                print(message)
        return self

    def _fit_fallback(self, images, labels, validation):
        """No PyTorch installed: train an MLP on the same pixels instead."""
        from sklearn.neural_network import MLPClassifier

        self.backend = "sklearn-mlp"
        print("PyTorch is not installed, so this cell trains a small dense neural network")
        print("(scikit-learn MLPClassifier) on the same pixels. The story is the same;")
        print("a CNN would additionally exploit the fact that neighbouring pixels are related.")
        self.network = MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=300, random_state=self.seed)
        self.network.fit(flatten(images), labels)
        self.history["epoch"] = list(range(1, len(self.network.loss_curve_) + 1))
        self.history["train_loss"] = list(self.network.loss_curve_)
        return self

    def predict_proba(self, images):
        if self.backend == "sklearn-mlp":
            return self.network.predict_proba(flatten(images))
        import torch

        self.network.eval()
        x = torch.tensor(images, dtype=torch.float32).unsqueeze(1)
        with torch.no_grad():
            return torch.softmax(self.network(x), dim=1).numpy()

    def predict(self, images):
        return self.predict_proba(images).argmax(axis=1)

    def parameter_count(self):
        if self.backend == "sklearn-mlp":
            return int(sum(w.size for w in self.network.coefs_) + sum(b.size for b in self.network.intercepts_))
        return int(sum(p.numel() for p in self.network.parameters()))
