from services.data.data_loader import fetch_market_data
from services.strategies.sma import sma_crossover
from services.backtesting.vectorized import run_vectorized_backtest
from services.features import add_technical_indicators


def run_pipeline(symbol="BTC-USD", strategy="sma"):
    # 1. Fetch data
    df = fetch_market_data(symbol=symbol)

    # 2. Add shared technical indicators before applying strategy
    try:
        df = add_technical_indicators(df)
    except Exception:
        pass

    # 3. Apply strategy
    if strategy == "sma":
        df = sma_crossover(df)
    else:
        raise ValueError("Unknown strategy")

    # 4. Run backtest
    results = run_vectorized_backtest(df)

    return results