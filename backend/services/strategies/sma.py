import pandas as pd


def sma_crossover(df: pd.DataFrame, fast=20, slow=50):
    df = df.copy()

    df["sma_fast"] = df["close"].rolling(fast).mean()
    df["sma_slow"] = df["close"].rolling(slow).mean()

    df["position"] = (df["sma_fast"] > df["sma_slow"]).astype(int)

    # critical: avoid look-ahead bias
    df["position"] = df["position"].shift(1)

    return df