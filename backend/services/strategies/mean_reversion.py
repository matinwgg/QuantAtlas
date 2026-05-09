import pandas as pd


def mean_reversion_strategy(df: pd.DataFrame, window=20, threshold=-1.0):
    df = df.copy()

    rolling_mean = df["close"].rolling(window).mean()
    rolling_std = df["close"].rolling(window).std()

    z_score = (df["close"] - rolling_mean) / rolling_std

    df["position"] = (z_score < threshold).astype(int)
    df["position"] = df["position"].shift(1)

    return df