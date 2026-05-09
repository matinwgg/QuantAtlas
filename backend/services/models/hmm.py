"""HMM regime detection utilities with graceful fallbacks.

This module attempts to use `hmmlearn` (preferred) and falls back to a
KMeans-based regime approximation when `hmmlearn` is not available.
"""
from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

import numpy as np


def fit_hmm(X: np.ndarray, n_components: int = 3, random_state: int = 0) -> Any:
    """Fit an HMM (GaussianHMM) or fall back to KMeans-based wrapper.

    Returns a fitted model exposing `predict(X)`.
    """
    try:
        from hmmlearn.hmm import GaussianHMM

        model = GaussianHMM(n_components=n_components, covariance_type="diag", n_iter=200, random_state=random_state)
        model.fit(X)
        return model
    except Exception:
        # fallback: KMeans clusterer with predict API
        try:
            from sklearn.cluster import KMeans

            km = KMeans(n_clusters=n_components, random_state=random_state).fit(X)

            class KMeansWrapper:
                def __init__(self, km):
                    self.km = km

                def predict(self, X):
                    return self.km.predict(X)

                def fit(self, X):
                    self.km.fit(X)

            return KMeansWrapper(km)
        except Exception as e:
            raise RuntimeError("Neither hmmlearn nor sklearn available to fit regimes") from e


def save_hmm(model: Any, path: str | Path):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "wb") as f:
        pickle.dump(model, f)


def load_hmm(path: str | Path) -> Any:
    with open(path, "rb") as f:
        return pickle.load(f)
