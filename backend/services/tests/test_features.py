import pandas as pd
import numpy as np

from services.features import add_technical_indicators, add_advanced_indicators, prepare_features_for_model


def make_sample_df():
    dates = pd.date_range("2020-01-01", periods=30)
    df = pd.DataFrame({
        "open": np.linspace(100, 130, 30),
        "high": np.linspace(101, 131, 30),
        "low": np.linspace(99, 129, 30),
        "close": np.linspace(100, 130, 30),
        "volume": np.arange(1000, 1030),
    }, index=dates)
    df.index.name = "date"
    return df


def test_add_technical_indicators_adds_columns():
    df = make_sample_df()
    out = add_technical_indicators(df)

    assert "sma_10" in out.columns
    assert "ema_12" in out.columns
    assert "rsi_14" in out.columns
    assert "macd" in out.columns


def test_short_history_technical_indicators_survive_dropna():
    df = make_sample_df().head(10)

    out = add_technical_indicators(df)
    prepared = prepare_features_for_model(out, dropna=True)

    assert prepared.shape[0] == 10
    assert not prepared[["sma_20", "sma_50", "rsi_14", "volatility_20"]].isna().any().any()


def test_add_advanced_indicators_adds_columns():
    df = make_sample_df()
    out = add_advanced_indicators(df)

    assert "bb_upper" in out.columns
    assert "bb_lower" in out.columns
    assert "obv" in out.columns
    assert "stoch_k" in out.columns


def test_prepare_features_for_model_imputes_and_drops():
    df = make_sample_df()
    df.loc[df.index[5], "close"] = np.nan

    out = prepare_features_for_model(df, dropna=False)
    assert out.shape[0] == 30

    out2 = prepare_features_for_model(df, dropna=True)
    assert out2.shape[0] <= 30
