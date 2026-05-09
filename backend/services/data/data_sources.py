"""
Market detection and data source routing
"""

from typing import Literal

MarketType = Literal["US", "GSE"]


def detect_market(symbol: str) -> MarketType:
    """
    Detect whether symbol belongs to:
    - US market (default)
    - Ghana Stock Exchange (GSE)

    Convention:
    - US: AAPL, TSLA, MSFT
    - GSE: GCB.GH, MTNGH, etc.
    """

    if not symbol:
        raise ValueError("Symbol cannot be empty")

    symbol = symbol.upper()

    # Ghana Stock Exchange heuristic
    if symbol.endswith(".GH") or symbol.endswith("GH"):
        return "GSE"

    return "US"