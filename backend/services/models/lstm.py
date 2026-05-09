"""Minimal PyTorch LSTM training and persistence helpers.

This module keeps imports lazy so the package can be imported even when
`torch` is not installed. Use `train_lstm_model` to train and `save_model`/
`load_model` to persist model artifacts.
"""
from __future__ import annotations

from pathlib import Path
from typing import Tuple, Any

import numpy as np


def _ensure_torch():
    try:
        import torch  # type: ignore
        import torch.nn as nn  # type: ignore
        import torch.utils.data as data  # type: ignore
        return torch, nn, data
    except Exception as e:
        raise RuntimeError("PyTorch is required for LSTM training. Install torch first.") from e


def _build_model(input_size: int, hidden_size: int = 32, num_layers: int = 1):
    torch, nn, _ = _ensure_torch()

    class LSTMModel(nn.Module):
        def __init__(self, input_size, hidden_size=32, num_layers=1):
            super().__init__()
            self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
            self.fc = nn.Linear(hidden_size, 1)

        def forward(self, x):
            out, _ = self.lstm(x)
            out = out[:, -1, :]
            out = self.fc(out)
            return out.squeeze(-1)

    return LSTMModel(input_size, hidden_size, num_layers)


def train_lstm_model(X: np.ndarray, y: np.ndarray, seq_len: int = 20, epochs: int = 5, batch_size: int = 64, lr: float = 1e-3, device: str | None = None) -> Tuple[Any, dict]:
    """Train an LSTM on sequences built from X to predict binary target y.

    X: array-like shape (n_samples, n_features)
    y: array-like shape (n_samples,) - binary labels (0/1) or floats
    Returns: (trained_model, metadata)
    """
    torch, nn, data = _ensure_torch()

    device = device or ("cuda" if torch.cuda.is_available() else "cpu")

    X = np.asarray(X)
    y = np.asarray(y)

    # build sequences
    sequences = []
    targets = []
    for i in range(len(X) - seq_len):
        sequences.append(X[i : i + seq_len])
        targets.append(y[i + seq_len])

    if len(sequences) == 0:
        raise RuntimeError("Not enough rows to build sequences with seq_len={}".format(seq_len))

    X_seq = torch.tensor(np.stack(sequences).astype(np.float32))
    y_seq = torch.tensor(np.array(targets).astype(np.float32))

    dataset = data.TensorDataset(X_seq, y_seq)
    loader = data.DataLoader(dataset, batch_size=batch_size, shuffle=True)

    model = _build_model(input_size=X.shape[1])
    model = model.to(device)

    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    for epoch in range(epochs):
        model.train()
        epoch_loss = 0.0
        for xb, yb in loader:
            xb = xb.to(device)
            yb = yb.to(device)
            optimizer.zero_grad()
            out = model(xb)
            loss = criterion(out, yb)
            loss.backward()
            optimizer.step()
            epoch_loss += float(loss.item()) * xb.size(0)

        epoch_loss /= len(dataset)

    metadata = {"input_size": X.shape[1], "seq_len": seq_len}
    return model, metadata


def save_model(model: Any, metadata: dict, path: str | Path):
    torch, _, _ = _ensure_torch()
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    state = {"state_dict": model.state_dict(), "metadata": metadata}
    torch.save(state, str(p))


def load_model(path: str | Path):
    torch, _, _ = _ensure_torch()
    state = torch.load(str(path), map_location="cpu")
    meta = state.get("metadata", {})
    model = _build_model(input_size=meta.get("input_size", 1))
    model.load_state_dict(state["state_dict"])
    return model, meta
