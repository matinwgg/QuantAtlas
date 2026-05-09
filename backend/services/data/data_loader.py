# import os
from pathlib import Path
# import json

import pandas as pd
import numpy as np

import yfinance as yf  # type: ignore

from .data_sources import detect_market

# Base data directory (relative to backend/)
BASE_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
RAW_DATA_DIR = BASE_DATA_DIR / "raw"


def _ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def fetch_us_data(symbol: str, period="2y", interval="1d", start: str | None = None, end: str | None = None):
    """Fetch US data via yfinance.

    Supports either `period` or (`start`, `end`). If `yfinance` is not
    installed, raises an informative error.
    """

    if yf is None:
        raise RuntimeError("yfinance is not available. Install with `pip install yfinance` to fetch live data.")

    if start or end:
        df = yf.download(symbol, start=start, end=end, interval=interval)
    else:
        df = yf.download(symbol, period=period, interval=interval)

    if df is None or df.empty:
        # return empty DataFrame rather than raising here so callers can decide
        return pd.DataFrame()

    # Handle MultiIndex columns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Normalize column names
    df.columns = [col.lower() for col in df.columns]

    df.index.name = "date"

    # Ensure required column exists
    if "close" not in df.columns:
        raise ValueError("Missing 'close' column in data")

    return df


def fetch_gse_data(symbol: str):
    """
    Placeholder for Ghana Stock Exchange data.

    For now, load from CSV:
    data/gse/{symbol}.csv

    Expected columns:
    date, open, high, low, close, volume
    """

    path = BASE_DATA_DIR / "gse" / f"{symbol}.csv"

    if not path.exists():
        raise FileNotFoundError(f"GSE CSV not found at {path}")

    df = pd.read_csv(path, parse_dates=["date"], index_col="date")

    return df


def add_returns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "close" not in df.columns:
        raise ValueError("Cannot compute returns: 'close' column missing")

    df["log_return"] = np.log(df["close"] / df["close"].shift(1))

    return df

def fetch_market_data(symbol: str, period="2y", interval="1d"):
    """Fetch market data for `symbol`.

    This is a lightweight facade that chooses the right source.
    For US symbols we may optionally read/update a local raw cache.
    """

    market = detect_market(symbol)

    if market == "US":
        df = fetch_us_data(symbol, period=period, interval=interval)
    elif market == "GSE":
        df = fetch_gse_data(symbol)
    else:
        raise ValueError("Unsupported market")

    # compute returns
    df = add_returns(df)

    return df


def _raw_cache_path(symbol: str, market: str) -> Path:
    return RAW_DATA_DIR / market.lower() / f"{symbol}.csv"


def load_raw_cache(symbol: str, market: str):
    path = _raw_cache_path(symbol, market)
    if not path.exists():
        return None
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    df.columns = [str(col).strip().lower() for col in df.columns]
    df.index.name = df.index.name or "date"
    return df


def save_raw_cache(df: pd.DataFrame, symbol: str, market: str):
    path = _raw_cache_path(symbol, market)
    _ensure_dir(path.parent)
    df.to_csv(path)


def update_raw_data(symbol: str, market: str, interval: str = "1d") -> pd.DataFrame:
    """Update local raw CSV cache for `symbol` by fetching only newer data.

    If no cache exists, fetch the full recent window via `fetch_us_data`.
    """
    # only implemented for US (yfinance) currently
    if market != "US":
        raise NotImplementedError("Incremental raw update currently only supported for US market")

    existing = load_raw_cache(symbol, market)

    if existing is None:
        # fetch a reasonable window (2y)
        df = fetch_us_data(symbol, period="2y", interval=interval)
        if df is None or df.empty:
            return pd.DataFrame()
        save_raw_cache(df, symbol, market)
        return df

    last_date = existing.index.max()

    # start from next calendar day to avoid duplicate index
    start = (pd.to_datetime(last_date) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

    new = fetch_us_data(symbol, start=start, interval=interval)

    if new is None or new.empty:
        return existing

    combined = pd.concat([existing, new])
    combined = combined[~combined.index.duplicated(keep="last")]
    combined = combined.sort_index()

    save_raw_cache(combined, symbol, market)

    return combined
