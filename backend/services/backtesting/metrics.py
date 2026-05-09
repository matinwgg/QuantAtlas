import numpy as np


def calculate_metrics(df):
    total_return = df["cumret_strategy"].iloc[-1] - 1
    bh_return = df["cumret_buyhold"].iloc[-1] - 1

    annual_return = (1 + total_return) ** (252 / len(df)) - 1
    annual_vol = df["strategy_return"].std() * np.sqrt(252)

    sharpe = annual_return / annual_vol if annual_vol > 0 else 0

    rolling_max = df["cumret_strategy"].cummax()
    drawdown = (df["cumret_strategy"] - rolling_max) / rolling_max

    max_dd = drawdown.min()

    return {
        "total_return": float(total_return),
        "buy_hold_return": float(bh_return),
        "annual_return": float(annual_return),
        "annual_volatility": float(annual_vol),
        "sharpe": float(sharpe),
        "max_drawdown": float(max_dd),
    }