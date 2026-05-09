"""Shared feature engineering utilities for QuantAtlas.

This module should be used by both training and inference paths to ensure
feature parity.
"""

from typing import Tuple
import pandas as pd
import numpy as np


def _rsi(series: pd.Series, window: int = 14) -> pd.Series:
    delta = series.diff().fillna(0)
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window, min_periods=1).mean()
    avg_loss = loss.rolling(window, min_periods=1).mean()

    rs = avg_gain / (avg_loss + 1e-9)
    rsi = 100 - 100 / (1 + rs)
    return rsi


def add_technical_indicators(
    df: pd.DataFrame,
    sma_windows: Tuple[int, ...] = (10, 20, 50),
    ema_windows: Tuple[int, ...] = (12, 26),
    rsi_window: int = 14,
) -> pd.DataFrame:
    """Add common technical indicators to `df` and return a new DataFrame.

    Adds:
    - SMA for each window in `sma_windows`
    - EMA for each window in `ema_windows`
    - RSI (single series)
    - MACD + signal
    - 20-day rolling volatility (std of pct_change)

    Keeps original index and columns; will forward/backfill as appropriate.
    """

    df = df.copy()

    if "close" not in df.columns:
        raise ValueError("add_technical_indicators requires a 'close' column")

    # SMA
    for w in sma_windows:
        df[f"sma_{w}"] = df["close"].rolling(w, min_periods=1).mean()

    # EMA
    for w in ema_windows:
        df[f"ema_{w}"] = df["close"].ewm(span=w, adjust=False).mean()

    # RSI
    df[f"rsi_{rsi_window}"] = _rsi(df["close"], window=rsi_window)

    # MACD
    fast = df["close"].ewm(span=ema_windows[0], adjust=False).mean()
    slow = df["close"].ewm(span=ema_windows[1], adjust=False).mean()
    df["macd"] = fast - slow
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()

    # Volatility
    returns = df["close"].pct_change().fillna(0)
    df["volatility_20"] = returns.rolling(20, min_periods=1).std(ddof=0)

    return df


def prepare_features_for_model(df: pd.DataFrame, dropna: bool = True) -> pd.DataFrame:
    """Minimal preparation before feeding features into models.

    - Ensures numeric dtypes for expected columns
    - Fills or drops NA per `dropna`
    - (Left intentionally lightweight — scaling should be handled by the model pipeline)
    """

    df = df.copy()

    # Convert common columns to numeric (safe coercion)
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Basic imputation: forward/back fill then optional dropna
    df = df.ffill().bfill()

    if dropna:
        df = df.dropna()

    return df


def add_advanced_indicators(df: pd.DataFrame, bb_window: int = 20, atr_window: int = 14, stoch_k_window: int = 14):
    """Adds Bollinger Bands, ATR, OBV, and Stochastic oscillator.

    Safe to call even when some columns are missing; missing-value tolerant.
    """

    df = df.copy()

    if "close" not in df.columns:
        raise ValueError("add_advanced_indicators requires a 'close' column")

    # Bollinger Bands
    ma = df["close"].rolling(bb_window).mean()
    msd = df["close"].rolling(bb_window).std()
    df["bb_upper"] = ma + 2 * msd
    df["bb_lower"] = ma - 2 * msd

    # ATR (requires high/low)
    if "high" in df.columns and "low" in df.columns:
        prev_close = df["close"].shift(1)
        tr1 = df["high"] - df["low"]
        tr2 = (df["high"] - prev_close).abs()
        tr3 = (df["low"] - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df[f"atr_{atr_window}"] = tr.rolling(atr_window).mean()

    # OBV
    if "volume" in df.columns:
        sign = np.sign(df["close"].diff()).fillna(0)
        df["obv"] = (sign * df["volume"]).cumsum()

    # Stochastic oscillator
    low_min = df["close"].rolling(stoch_k_window).min()
    high_max = df["close"].rolling(stoch_k_window).max()
    denom = (high_max - low_min).replace(0, np.nan)
    df["stoch_k"] = (df["close"] - low_min) / denom * 100
    df["stoch_d"] = df["stoch_k"].rolling(3).mean()

    return df
