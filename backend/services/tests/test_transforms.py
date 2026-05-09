import pandas as pd
import numpy as np
from services.transforms import SimpleStandardScaler, SimpleMinMaxScaler, TransformPipeline


def make_df():
    dates = pd.date_range("2020-01-01", periods=10)
    df = pd.DataFrame({
        "a": np.arange(10).astype(float),
        "b": np.linspace(10, 20, 10),
    }, index=dates)
    df.index.name = "date"
    return df


def test_standard_scaler_center_scale():
    df = make_df()
    scaler = SimpleStandardScaler()
    out = scaler.fit_transform(df)

    # mean approx 0
    assert abs(out["a"].mean()) < 1e-9
    assert abs(out["b"].mean()) < 1e-9


def test_minmax_scaler_range():
    df = make_df()
    scaler = SimpleMinMaxScaler()
    out = scaler.fit_transform(df)

    assert abs(out["a"].min() - 0.0) < 1e-9
    assert abs(out["a"].max() - 1.0) < 1e-9


def test_pipeline_save_load(tmp_path):
    df = make_df()
    pipe = TransformPipeline()
    pipe.fit(df)

    p = tmp_path / "pipe.json"
    pipe.save(str(p))

    loaded = TransformPipeline.load(str(p))
    out = loaded.transform(df)
    assert list(out.columns) == list(df.columns)
