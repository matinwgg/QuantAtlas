"""Training helpers for fitting and persisting TransformPipeline artifacts.

These utilities are used during model training to fit a scaler/pipeline on
historical features and persist the parameters for inference-time usage.
"""
from typing import Optional, Iterable
from pathlib import Path

import pandas as pd
import numpy as np

from services.feature_store import get_features, pipeline_path, _ensure_dir
from services.transforms import TransformPipeline


def train_and_save_pipeline(symbol: str, feature_columns: Optional[Iterable[str]] = None, overwrite: bool = False, refresh: bool = False) -> TransformPipeline:
    """Fit a TransformPipeline on `symbol` features and persist it.

    - `feature_columns`: optional list of column names to include. If omitted,
      numeric columns from the feature DataFrame will be used.
    - `overwrite`: if True, overwrite any existing pipeline artifact.
    """
    # Get prepared features (do not apply any existing pipeline)
    # By default we avoid forcing an external fetch; set `refresh=True` to
    # update the raw cache before fitting.
    # do not drop rows with NaNs introduced by long-window indicators when
    # fitting the scaler; allow fitting on available numeric columns.
    df = get_features(symbol, refresh=refresh, apply_pipeline=False, dropna=False)

    if df is None or df.empty:
        raise RuntimeError(f"No feature data available for symbol={symbol}")

    if feature_columns is None:
        feature_columns = df.select_dtypes(include=[np.number]).columns.tolist()

    feature_columns = [c for c in feature_columns if c in df.columns]

    if not feature_columns:
        raise RuntimeError("No numeric feature columns found to fit pipeline")

    # Fit a default TransformPipeline (SimpleStandardScaler inside)
    pipeline = TransformPipeline()
    pipeline.fit(df.loc[:, feature_columns])

    # persist
    path = pipeline_path(symbol)
    _ensure_dir(path.parent)
    if path.exists() and not overwrite:
        # return existing pipeline
        return TransformPipeline.load(str(path))

    pipeline.save(str(path))

    return pipeline
