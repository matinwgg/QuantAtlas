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
    """Run a research backtest for a validated strategy and symbol."""
    symbol = request.GET.get("symbol", "AAPL").strip().upper()
    strategy = request.GET.get("strategy", "sma").strip().lower()

    if not symbol or len(symbol) > 20:
        return Response({"error": "Invalid symbol"}, status=400)

    try:
        validate_strategy(strategy)
        df = fetch_market_data(symbol)
        if df.empty:
            return Response({"error": "No market data available"}, status=404)

        # Indicators are required by some strategies; failures must not be
        # silently converted into a different research result.
        df = add_technical_indicators(df)

        if strategy == "sma":
            df = sma_crossover(df)
        elif strategy == "momentum":
            df = momentum_strategy(df)
        elif strategy == "mean_reversion":
            df = mean_reversion_strategy(df)

        result = run_vectorized_backtest(df)
        return Response({"symbol": symbol, "strategy": strategy, "results": result})

    except ValueError as exc:
        return Response({"error": str(exc)}, status=400)
    except Exception:
        # Do not expose provider/library/internal exception details to clients.
        return Response({"error": "Unable to run backtest"}, status=500)
