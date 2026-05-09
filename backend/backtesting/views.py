from rest_framework.decorators import api_view
from rest_framework.response import Response

from services.data.data_loader import fetch_market_data
from services.strategies.sma import sma_crossover
from services.strategies.momentum import momentum_strategy
from services.strategies.mean_reversion import mean_reversion_strategy
from services.backtesting.vectorized import run_vectorized_backtest
from services.utils.helpers import validate_strategy
from services.features import add_technical_indicators


@api_view(["GET"])
def run_backtest(request):
    symbol = request.GET.get("symbol", "AAPL")
    strategy = request.GET.get("strategy", "sma")

    try:
        validate_strategy(strategy)

        df = fetch_market_data(symbol)

        # ensure shared technical indicators are available for strategies and models
        try:
            df = add_technical_indicators(df)
        except Exception:
            # non-fatal: continue with original df if indicators fail
            pass

        if strategy == "sma":
            df = sma_crossover(df)

        elif strategy == "momentum":
            df = momentum_strategy(df)

        elif strategy == "mean_reversion":
            df = mean_reversion_strategy(df)

        result = run_vectorized_backtest(df)

        return Response({
            "symbol": symbol,
            "strategy": strategy,
            "results": result
        })

    except Exception as e:
        return Response({"error": str(e)}, status=400)