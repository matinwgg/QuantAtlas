"""Vectorized long-only backtesting for daily strategy returns."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .metrics import calculate_metrics


def run_vectorized_backtest(df: pd.DataFrame, risk_free_rate: float = 0.0) -> dict:
    """Run a long-only backtest on ``position`` and ``log_return`` columns.

    ``position`` is expected to be aligned to the return it earns. Strategy
    helpers in this repository already shift their signal by one day, so this
    function does not shift again. Fractional positions in ``[0, 1]`` are
    accepted to support probability-sized allocations.

    Returns a JSON-serialisable payload containing metrics, the observation
    window, and an equity curve. Raises ``ValueError`` when the input cannot
    produce a meaningful result.
    """
    required_cols = ["position", "log_return"]

    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    data = df.loc[:, required_cols].copy()
    data["position"] = pd.to_numeric(data["position"], errors="coerce")
    data["log_return"] = pd.to_numeric(data["log_return"], errors="coerce")
    data = data.replace([np.inf, -np.inf], np.nan).dropna()

    if data.empty:
        raise ValueError("No valid rows available for backtesting")

    positions = data["position"].to_numpy(dtype=float)
    returns = data["log_return"].to_numpy(dtype=float)

    if not np.isfinite(positions).all() or not np.isfinite(returns).all():
        raise ValueError("Backtest inputs must be finite numbers")

    if (positions < 0).any() or (positions > 1).any():
        raise ValueError("position must be between 0 and 1 for a long-only backtest")

    data["strategy_return"] = positions * returns
    data["cumret_strategy"] = np.exp(np.cumsum(data["strategy_return"].to_numpy(dtype=float)))
    data["cumret_buyhold"] = np.exp(np.cumsum(returns))

    metrics = calculate_metrics(data, risk_free_rate=risk_free_rate)
    metrics["observations"] = int(len(data))
    metrics["start"] = str(data.index[0])
    metrics["end"] = str(data.index[-1])

    equity_curve = [
        {
            "date": str(index),
            "strategy": float(row.cumret_strategy),
            "buyhold": float(row.cumret_buyhold),
        }
        for index, row in data.iterrows()
    ]

    return {"metrics": metrics, "equity_curve": equity_curve}
