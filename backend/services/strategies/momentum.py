import pandas as pd


def momentum_strategy(df: pd.DataFrame, window=20):
    df = df.copy()

    df["momentum"] = df["close"].pct_change(window)

    df["position"] = (df["momentum"] > 0).astype(int)
    df["position"] = df["position"].shift(1)

    return df