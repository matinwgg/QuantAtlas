"""Simple transform pipeline and lightweight scalers for models.

Avoids external dependencies so tests and basic inference can run without
scikit-learn. Scaler parameters are JSON-serializable via `to_dict()`.
"""
from __future__ import annotations

from typing import Iterable, List, Optional, Dict, Any
from pathlib import Path
import json

import pandas as pd
import numpy as np


class SimpleStandardScaler:
    def __init__(self, columns: Optional[List[str]] = None):
        self.columns = columns
        self.mean_: Optional[Dict[str, float]] = None
        self.scale_: Optional[Dict[str, float]] = None

    def fit(self, df: pd.DataFrame, columns: Optional[Iterable[str]] = None):
        if columns is None:
            columns = self.columns or df.select_dtypes(include=[np.number]).columns.tolist()
        s = df.loc[:, list(columns)].astype(float)
        mean = s.mean()
        std = s.std(ddof=0).replace(0, 1e-9)
        self.mean_ = {c: float(mean[c]) for c in s.columns}
        self.scale_ = {c: float(std[c]) for c in s.columns}
        self.columns = list(s.columns)
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.mean_ is None or self.scale_ is None:
            raise RuntimeError("Scaler not fitted")
        df = df.copy()
        for c in self.columns:
            if c in df.columns:
                df[c] = (df[c].astype(float) - self.mean_.get(c, 0.0)) / self.scale_.get(c, 1.0)
        return df

    def fit_transform(self, df: pd.DataFrame, columns: Optional[Iterable[str]] = None) -> pd.DataFrame:
        return self.fit(df, columns).transform(df)

    def to_dict(self) -> Dict[str, Any]:
        return {"columns": self.columns, "mean": self.mean_, "scale": self.scale_}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SimpleStandardScaler":
        obj = cls(columns=d.get("columns"))
        obj.mean_ = {k: float(v) for k, v in (d.get("mean") or {}).items()}
        obj.scale_ = {k: float(v) for k, v in (d.get("scale") or {}).items()}
        return obj


class SimpleMinMaxScaler:
    def __init__(self, columns: Optional[List[str]] = None):
        self.columns = columns
        self.min_: Optional[Dict[str, float]] = None
        self.range_: Optional[Dict[str, float]] = None

    def fit(self, df: pd.DataFrame, columns: Optional[Iterable[str]] = None):
        if columns is None:
            columns = self.columns or df.select_dtypes(include=[np.number]).columns.tolist()
        s = df.loc[:, list(columns)].astype(float)
        mn = s.min()
        mx = s.max()
        rng = (mx - mn).replace(0, 1e-9)
        self.min_ = {c: float(mn[c]) for c in s.columns}
        self.range_ = {c: float(rng[c]) for c in s.columns}
        self.columns = list(s.columns)
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.min_ is None or self.range_ is None:
            raise RuntimeError("Scaler not fitted")
        df = df.copy()
        for c in self.columns:
            if c in df.columns:
                df[c] = (df[c].astype(float) - self.min_.get(c, 0.0)) / self.range_.get(c, 1.0)
        return df

    def fit_transform(self, df: pd.DataFrame, columns: Optional[Iterable[str]] = None) -> pd.DataFrame:
        return self.fit(df, columns).transform(df)

    def to_dict(self) -> Dict[str, Any]:
        return {"columns": self.columns, "min": self.min_, "range": self.range_}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SimpleMinMaxScaler":
        obj = cls(columns=d.get("columns"))
        obj.min_ = {k: float(v) for k, v in (d.get("min") or {}).items()}
        obj.range_ = {k: float(v) for k, v in (d.get("range") or {}).items()}
        return obj


class TransformPipeline:
    """Composes a single scaler into a lightweight pipeline.

    Supports saving/loading scaler parameters to JSON.
    """

    def __init__(self, scaler: Optional[object] = None):
        self.scaler = scaler or SimpleStandardScaler()

    def fit(self, df: pd.DataFrame, columns: Optional[Iterable[str]] = None):
        self.scaler.fit(df, columns)
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.scaler.transform(df)

    def fit_transform(self, df: pd.DataFrame, columns: Optional[Iterable[str]] = None) -> pd.DataFrame:
        return self.fit(df, columns).transform(df)

    def save(self, path: str):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"scaler": self.scaler.to_dict()}, f)

    @classmethod
    def load(cls, path: str) -> "TransformPipeline":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        scaler_dict = data.get("scaler", {})
        # detect scaler type heuristically
        if "mean" in scaler_dict and "scale" in scaler_dict:
            scaler = SimpleStandardScaler.from_dict(scaler_dict)
        elif "min" in scaler_dict and "range" in scaler_dict:
            scaler = SimpleMinMaxScaler.from_dict(scaler_dict)
        else:
            scaler = SimpleStandardScaler.from_dict(scaler_dict)

        return cls(scaler=scaler)
