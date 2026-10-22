"""AlphaVantage connector (minimal, no external data dependencies)."""

from __future__ import annotations

import os
from typing import Optional

import pandas as pd
import requests

API_URL = "https://www.alphavantage.co/query"


def _clean_col(name: str) -> str:
    parts = name.split(". ")
    if len(parts) > 1:
        name = parts[1]
    return name.strip().lower().replace(" ", "_")


def fetch_daily_adjusted(
    symbol: str,
    api_key: Optional[str] = None,
    outputsize: str = "compact",
    timeout: int = 10,
) -> pd.DataFrame:
    """Fetch TIME_SERIES_DAILY_ADJUSTED from AlphaVantage.

    Requires an API key via argument or ``ALPHAVANTAGE_API_KEY``. The key is
    sent as a query parameter because that is the provider's API; do not log
    the constructed URL.
    """
    if api_key is None:
        api_key = os.environ.get("ALPHAVANTAGE_API_KEY")
    if not api_key:
        raise RuntimeError("AlphaVantage API key not provided (env ALPHAVANTAGE_API_KEY)")

    params = {
        "function": "TIME_SERIES_DAILY_ADJUSTED",
        "symbol": symbol,
        "outputsize": outputsize,
        "apikey": api_key,
        "datatype": "json",
    }

    response = requests.get(API_URL, params=params, timeout=timeout)
    response.raise_for_status()
    data = response.json()

    ts_key = next((key for key in data if "Time Series" in key), None)
    if ts_key is None:
        message = data.get("Note") or data.get("Error Message") or "unknown provider error"
        raise RuntimeError(f"AlphaVantage response missing time series: {message}")

    df = pd.DataFrame.from_dict(data[ts_key], orient="index")
    df.columns = [_clean_col(col) for col in df.columns]

    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df.index = pd.to_datetime(df.index)
    df.index.name = "date"
    return df.sort_index()
