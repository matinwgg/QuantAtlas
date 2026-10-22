"""Performance metrics for vectorized daily backtests."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


def calculate_metrics(df: pd.DataFrame, risk_free_rate: float = 0.0) -> dict:
    """Calculate standard long-only performance metrics.

    ``df`` must contain ``strategy_return``, ``position``, ``cumret_strategy``,
    and ``cumret_buyhold``. Returns are daily log returns; the Sharpe ratio is
    computed from daily simple excess returns and annualised with 252 trading
    days. ``risk_free_rate`` is an annual simple rate.
    """
    if df.empty:
        raise ValueError("Cannot calculate metrics for an empty backtest")

    required = ["strategy_return", "position", "cumret_strategy", "cumret_buyhold"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    strategy_return = pd.to_numeric(df["strategy_return"], errors="coerce").astype(float)
    if strategy_return.isna().any() or not np.isfinite(strategy_return).all():
        raise ValueError("strategy_return contains non-finite values")

    observations = int(len(df))
    final_strategy = float(df["cumret_strategy"].iloc[-1])
    final_buyhold = float(df["cumret_buyhold"].iloc[-1])

    if final_strategy <= 0 or final_buyhold <= 0:
        raise ValueError("Cumulative equity must be positive")

    total_return = final_strategy - 1.0
    bh_return = final_buyhold - 1.0

    # CAGR from the compounded equity curve. Guard the one-row case.
    annual_return = final_strategy ** (252.0 / observations) - 1.0 if observations > 0 else 0.0

    daily_vol = float(strategy_return.std(ddof=1)) if observations > 1 else 0.0
    annual_vol = daily_vol * math.sqrt(252.0)

    daily_rf = (1.0 + risk_free_rate) ** (1.0 / 252.0) - 1.0
    excess = strategy_return - daily_rf
    excess_vol = float(excess.std(ddof=1)) if observations > 1 else 0.0
    sharpe = float(excess.mean() / excess_vol * math.sqrt(252.0)) if excess_vol > 0 else 0.0

    equity = pd.to_numeric(df["cumret_strategy"], errors="coerce").astype(float)
    rolling_max = equity.cummax().replace(0, np.nan)
    drawdown = equity / rolling_max - 1.0
    max_dd = float(drawdown.min()) if drawdown.notna().any() else 0.0

    positions = pd.to_numeric(df["position"], errors="coerce").astype(float)
    turnover = float(positions.diff().abs().sum()) if observations > 1 else 0.0
    trades = int((positions.diff().abs() > 0).sum()) if observations > 1 else 0

    return {
        "total_return": float(total_return),
        "buy_hold_return": float(bh_return),
        "annual_return": float(annual_return),
        "annual_volatility": float(annual_vol),
        "sharpe": float(sharpe),
        "max_drawdown": float(max_dd),
        "turnover": float(turnover),
        "trades": trades,
    }
