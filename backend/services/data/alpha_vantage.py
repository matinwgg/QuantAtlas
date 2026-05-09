"""AlphaVantage connector (minimal, no external deps).

Provides a small helper to fetch daily adjusted time series.
"""
import os
import json
from urllib import request, parse
from typing import Optional

import pandas as pd


API_URL = "https://www.alphavantage.co/query"


def _clean_col(name: str) -> str:
    parts = name.split('. ')
    if len(parts) > 1:
        name = parts[1]
    name = name.strip().lower().replace(' ', '_')
    return name


def fetch_daily_adjusted(symbol: str, api_key: Optional[str] = None, outputsize: str = 'compact') -> pd.DataFrame:
    """Fetch TIME_SERIES_DAILY_ADJUSTED from AlphaVantage and return a DataFrame.

    Requires an API key via argument or `ALPHAVANTAGE_API_KEY` env var.
    """
    if api_key is None:
        api_key = os.environ.get('ALPHAVANTAGE_API_KEY')
    if not api_key:
        raise RuntimeError('AlphaVantage API key not provided (env ALPHAVANTAGE_API_KEY)')

    params = {
        'function': 'TIME_SERIES_DAILY_ADJUSTED',
        'symbol': symbol,
        'outputsize': outputsize,
        'apikey': api_key,
        'datatype': 'json',
    }

    url = API_URL + '?' + parse.urlencode(params)

    with request.urlopen(url) as resp:
        raw = resp.read()
        data = json.loads(raw.decode('utf-8'))

    # Find the time series key
    ts_key = None
    for k in data.keys():
        if 'Time Series' in k or 'Time Series' in k:
            ts_key = k
            break

    if ts_key is None:
        # API may return an error message
        raise RuntimeError(f"AlphaVantage response missing time series: {data.get('Note') or data.get('Error Message')}")

    timeseries = data[ts_key]

    df = pd.DataFrame.from_dict(timeseries, orient='index')

    # rename columns
    df.columns = [_clean_col(c) for c in df.columns]

    # convert to numeric where possible
    for c in df.columns:
        try:
            df[c] = pd.to_numeric(df[c], errors='coerce')
        except Exception:
            pass

    df.index = pd.to_datetime(df.index)
    df.index.name = 'date'

    return df.sort_index()
