import numpy as np
from .metrics import calculate_metrics


def run_vectorized_backtest(df):
    required_cols = ["position", "log_return"]

    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    df = df.dropna(subset=required_cols).copy()