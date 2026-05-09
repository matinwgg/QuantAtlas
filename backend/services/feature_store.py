"""Feature store facade for QuantAtlas.

Provides functions to produce and cache feature DataFrames for models and
backtesting. Uses `services.features` transforms and `services.data` for raw
ingestion.
"""
from pathlib import Path
from typing import Optional

import pandas as pd

from .features import add_technical_indicators, prepare_features_for_model
from .data.data_loader import (
    detect_market,
    fetch_market_data,
    load_raw_cache,
    update_raw_data,
)


BASE_FEATURE_DIR = Path(__file__).resolve().parents[2] / "data" / "features"
from .transforms import TransformPipeline

PIPELINE_DIR = Path(__file__).resolve().parents[2] / "models" / "pipelines"


def _ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def feature_cache_path(symbol: str) -> Path:
    return BASE_FEATURE_DIR / f"{symbol}.parquet"


def pipeline_path(symbol: str) -> Path:
    return PIPELINE_DIR / f"{symbol}_pipeline.json"


def load_pipeline(symbol: str) -> TransformPipeline | None:
    p = pipeline_path(symbol)
    if not p.exists():
        return None
    try:
        return TransformPipeline.load(str(p))
    except Exception:
        return None


def save_pipeline(symbol: str, pipeline: TransformPipeline):
    _ensure_dir(PIPELINE_DIR)
    pipeline.save(str(pipeline_path(symbol)))


def get_features(symbol: str, start: Optional[str] = None, end: Optional[str] = None, refresh: bool = False, limit: Optional[int] = None, apply_pipeline: bool = True, dropna: bool = True) -> pd.DataFrame:
    """Return a feature DataFrame for `symbol`.

    - If `refresh` is True, attempt to update raw cache (US symbols).
    - Applies `add_technical_indicators` and `prepare_features_for_model`.
    - Caches processed features to `data/features/{symbol}.parquet`.
    """
    market = detect_market(symbol)

    # update raw cache for US symbols if requested
    if refresh and market == "US":
        raw = update_raw_data(symbol, market)
    else:
        raw = load_raw_cache(symbol, market)

    # If no cached raw, fetch directly (non-cached path)
    if raw is None or raw.empty:
        raw = fetch_market_data(symbol)

    df = raw.copy()

    # Filter by start/end if provided
    if start is not None:
        df = df[df.index >= pd.to_datetime(start)]
    if end is not None:
        df = df[df.index <= pd.to_datetime(end)]

    # Add technical indicators (shared transform)
    df = add_technical_indicators(df)

    # Minimal cleanup ready for models
    df = prepare_features_for_model(df, dropna=dropna)

    # Apply a saved TransformPipeline (if available) so inference uses the
    # same scaler/transform parameters that were fitted during training.
    if apply_pipeline:
        pipeline = load_pipeline(symbol)
        if pipeline is not None:
            try:
                df = pipeline.transform(df)
            except Exception:
                # non-fatal: continue with untransformed features
                pass

    # persist features cache
    _ensure_dir(BASE_FEATURE_DIR)
    try:
        df.to_parquet(feature_cache_path(symbol))
    except Exception:
        # parquet may not be available; fallback to csv
        df.to_csv(feature_cache_path(symbol).with_suffix('.csv'))

    if limit:
        return df.tail(limit)

    return df
