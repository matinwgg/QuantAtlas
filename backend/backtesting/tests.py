from unittest.mock import patch

import pandas as pd
from django.test import TestCase

from services.data.data_loader import add_returns


def market_frame():
    dates = pd.date_range("2024-01-01", periods=90)
    close = [100 + (i * 0.5) + (2 if i % 7 == 0 else -1) for i in range(len(dates))]
    frame = pd.DataFrame(
        {
            "open": close,
            "high": [value + 1 for value in close],
            "low": [value - 1 for value in close],
            "close": close,
            "volume": [1_000 + i for i in range(len(dates))],
        },
        index=dates,
    )
    frame.index.name = "date"
    return add_returns(frame)


class BacktestApiTests(TestCase):
    @patch("backtesting.views.fetch_market_data")
    def test_backtest_returns_metrics(self, fetch_market_data):
        fetch_market_data.return_value = market_frame()

        response = self.client.get(
            "/api/backtest/run/?symbol=TESTSYM&strategy=sma",
            secure=True,
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["symbol"], "TESTSYM")
        self.assertEqual(payload["strategy"], "sma")
        self.assertIsNotNone(payload["results"])
        self.assertGreater(payload["results"]["metrics"]["observations"], 0)

    def test_invalid_symbol_is_rejected(self):
        response = self.client.get(
            "/api/backtest/run/?symbol=../../etc/passwd&strategy=sma",
            secure=True,
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_strategy_is_rejected(self):
        response = self.client.get(
            "/api/backtest/run/?symbol=AAPL&strategy=unknown",
            secure=True,
        )
        self.assertEqual(response.status_code, 400)

    def test_feature_refresh_requires_authentication(self):
        response = self.client.get(
            "/api/features/get/?symbol=AAPL&refresh=true",
            secure=True,
        )
        self.assertEqual(response.status_code, 403)

    def test_feature_limit_is_bounded(self):
        response = self.client.get(
            "/api/features/get/?symbol=AAPL&limit=100000",
            secure=True,
        )
        self.assertEqual(response.status_code, 400)
