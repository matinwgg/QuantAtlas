import math

import numpy as np
import pandas as pd
import pytest

from services.backtesting.metrics import calculate_metrics
from services.backtesting.vectorized import run_vectorized_backtest


def sample_frame():
    return pd.DataFrame(
        {
            "position": [0.0, 1.0, 1.0],
            "log_return": [0.0, 0.1, -0.05],
        },
        index=pd.date_range("2024-01-01", periods=3),
    )


def test_backtest_returns_metrics_and_equity_curve():
    result = run_vectorized_backtest(sample_frame())

    metrics = result["metrics"]
    assert metrics["observations"] == 3
    assert metrics["total_return"] == pytest.approx(math.exp(0.05) - 1.0)
    assert metrics["buy_hold_return"] == pytest.approx(math.exp(0.05) - 1.0)
    assert metrics["turnover"] == pytest.approx(1.0)
    assert metrics["trades"] == 1
    assert len(result["equity_curve"]) == 3
    assert result["equity_curve"][-1]["strategy"] == pytest.approx(math.exp(0.05))


def test_backtest_rejects_missing_columns():
    with pytest.raises(ValueError, match="Missing required column"):
        run_vectorized_backtest(pd.DataFrame({"position": [1.0]}))


def test_backtest_rejects_empty_data():
    df = sample_frame()
    df["log_return"] = np.nan
    with pytest.raises(ValueError, match="No valid rows"):
        run_vectorized_backtest(df)


def test_backtest_rejects_short_positions():
    df = sample_frame()
    df.loc[df.index[1], "position"] = 1.5
    with pytest.raises(ValueError, match="between 0 and 1"):
        run_vectorized_backtest(df)


def test_metrics_reject_empty_frame():
    with pytest.raises(ValueError, match="empty backtest"):
        calculate_metrics(pd.DataFrame())


def test_metrics_are_json_safe():
    result = run_vectorized_backtest(sample_frame())
    for value in result["metrics"].values():
        if isinstance(value, float):
            assert math.isfinite(value)
