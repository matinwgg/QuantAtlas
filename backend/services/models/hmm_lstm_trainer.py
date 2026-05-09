"""Trainer that orchestrates HMM regime fitting and LSTM training.

This script ties together the feature store, pipeline persistence, HMM
regime detection, and LSTM training. It saves artifacts to `backend/models/`.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional
import numpy as np

from services.feature_store import get_features, save_pipeline
from services.models.train_pipeline import train_and_save_pipeline
from services.models import registry


def _models_dir():
    return Path(__file__).resolve().parents[3] / "models" / "artifacts"


def train_hmm_lstm(
    symbol: str,
    seq_len: int = 20,
    hmm_components: int = 3,
    lstm_epochs: int = 5,
    feature_columns: Optional[List[str]] = None,
    refresh_pipeline: bool = True,
):
    """End-to-end training pipeline.

    Steps:
    - Fit & persist TransformPipeline (scaler)
    - Load features and apply pipeline
    - Fit HMM (or fallback) to detect regimes
    - Save HMM artifact
    - Add regime to features and train LSTM to predict next-day direction
    - Save LSTM artifact and register models
    """
    # 1) Fit and persist pipeline
    training_pipeline = train_and_save_pipeline(symbol, overwrite=True, refresh=refresh_pipeline)
    save_pipeline(symbol, training_pipeline)

    # 2) Load features with pipeline applied
    df = get_features(symbol, refresh=False, apply_pipeline=True, dropna=False)

    if df is None or df.empty:
        raise RuntimeError(f"No features available for {symbol}")

    # choose numeric columns for modeling if not provided
    if feature_columns is None:
        feature_columns = df.select_dtypes(include=[np.number]).columns.tolist()

    # ensure log_return and numeric columns present
    if "log_return" not in df.columns:
        raise RuntimeError("'log_return' must be present in features for target creation")

    X = df.loc[:, feature_columns].copy()

    # drop rows without numeric data
    X = X.dropna()

    # HMM fitting
    try:
        from services.models.hmm import fit_hmm, save_hmm

        hmm_model = fit_hmm(X.values, n_components=hmm_components)
        models_dir = _models_dir()
        models_dir.mkdir(parents=True, exist_ok=True)
        hmm_path = models_dir / f"{symbol}_hmm.pkl"
        save_hmm(hmm_model, hmm_path)
    except Exception as e:
        raise RuntimeError(f"HMM fitting failed: {e}") from e

    # attach regimes to features
    try:
        regimes = hmm_model.predict(X.values)
        X = X.iloc[len(X) - len(regimes) :].copy()
        X["regime"] = regimes
    except Exception:
        # if predict is not available, skip
        X["regime"] = 0

    # Prepare sequences and targets for LSTM
    # target: next-day up or down
    y = (df["log_return"].shift(-1) > 0).astype(float)
    full = X.join(y.rename("target")).dropna()

    if len(full) < seq_len + 1:
        raise RuntimeError("Not enough data to build LSTM sequences; try a shorter seq_len or more data")

    X_vals = full.loc[:, feature_columns + ["regime"]].values
    y_vals = full["target"].values

    # Train LSTM (lazy import inside)
    try:
        from services.models.lstm import train_lstm_model, save_model

        model, meta = train_lstm_model(X_vals, y_vals, seq_len=seq_len, epochs=lstm_epochs)
        lstm_path = models_dir / f"{symbol}_lstm.pt"
        save_model(model, meta, lstm_path)
    except Exception as e:
        raise RuntimeError(f"LSTM training failed: {e}") from e

    # Register artifacts in the simple in-memory registry
    registry.register(symbol, {
        "hmm": str(hmm_path),
        "lstm": str(lstm_path),
        "pipeline": str(Path(__file__).resolve().parents[3] / "models" / "pipelines" / f"{symbol}_pipeline.json"),
    })

    return {"hmm": str(hmm_path), "lstm": str(lstm_path)}
