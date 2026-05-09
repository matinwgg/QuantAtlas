import pandas as pd
import pytest
import math

from services.data.data_loader import add_returns
from services.data.data_sources import detect_market


def test_add_returns_computes_log_return():
    df = pd.DataFrame({"close": [100.0, 110.0, 105.0, 115.0]}, index=pd.date_range("2020-01-01", periods=4))

    out = add_returns(df)

    assert "log_return" in out.columns
    assert pd.isna(out["log_return"].iloc[0])

    expected = math.log(110.0 / 100.0)
    assert abs(out["log_return"].iloc[1] - expected) < 1e-9


def test_add_returns_missing_close_raises():
    df = pd.DataFrame({"open": [1, 2, 3]})
    with pytest.raises(ValueError):
        add_returns(df)


def test_detect_market_variants():
    assert detect_market("AAPL") == "US"
    assert detect_market("GCB.GH") == "GSE"
    assert detect_market("mtngh") == "GSE"

    with pytest.raises(ValueError):
        detect_market("")
