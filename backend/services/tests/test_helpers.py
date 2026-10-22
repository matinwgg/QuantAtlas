import pytest

from services.utils.helpers import (
    parse_bool,
    parse_int,
    parse_iso_date,
    validate_strategy,
    validate_symbol,
)


def test_validate_symbol_accepts_common_symbols():
    assert validate_symbol(" aapl ") == "AAPL"
    assert validate_symbol("BTC-USD") == "BTC-USD"
    assert validate_symbol("GCB.GH") == "GCB.GH"


@pytest.mark.parametrize("symbol", ["", "../AAPL", "A/B", "A" * 21, "AAPL;rm"])
def test_validate_symbol_rejects_unsafe_values(symbol):
    with pytest.raises(ValueError):
        validate_symbol(symbol)


def test_validate_strategy_rejects_unknown_values():
    assert validate_strategy("SMA") == "sma"
    with pytest.raises(ValueError):
        validate_strategy("buy-and-hope")


def test_parse_int_bounds():
    assert parse_int(None, name="limit", default=10, minimum=1, maximum=20) == 10
    assert parse_int("3", name="limit", default=10, minimum=1, maximum=20) == 3
    with pytest.raises(ValueError):
        parse_int("0", name="limit", default=10, minimum=1, maximum=20)
    with pytest.raises(ValueError):
        parse_int("abc", name="limit", default=10, minimum=1, maximum=20)


def test_parse_iso_date():
    assert parse_iso_date("2024-01-31", name="start") == "2024-01-31"
    assert parse_iso_date(None, name="start") is None
    with pytest.raises(ValueError):
        parse_iso_date("31/01/2024", name="start")


def test_parse_bool():
    assert parse_bool(None, default=True) is True
    assert parse_bool("false") is False
    assert parse_bool("YES") is True
    assert parse_bool(False) is False
    with pytest.raises(ValueError):
        parse_bool("maybe")
