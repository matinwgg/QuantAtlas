"""Placeholder HMM-LSTM model wrapper.

This file provides a minimal, importable scaffold for the hybrid model. Replace
placeholder logic with actual HMM + regime-conditioned LSTM training and
inference later.
"""

import pandas as pd
from .base import ModelBase


class HMM_LSTM_Model(ModelBase):
    def __init__(self, model_path: str | None = None):
        self.model_path = model_path

    def infer(self, df: pd.DataFrame) -> pd.DataFrame:
        """A safe placeholder inference that returns a `position` column.

        Currently uses a short-window momentum proxy until the real model is
        implemented. This keeps integration with the backtester simple.
        """

        df = df.copy()

        if "close" not in df.columns:
            raise ValueError("Input dataframe must contain 'close' column")

        # Simple proxy: buy when 5-day return positive (shifted to avoid look-ahead)
        df["position"] = (df["close"].pct_change(5) > 0).astype(int)
        df["position"] = df["position"].shift(1)

        return df


def load_model(path: str | None = None) -> HMM_LSTM_Model:
    # In future, load actual artifacts here
    return HMM_LSTM_Model(model_path=path)
