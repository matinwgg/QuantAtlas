"""Validation helpers shared by API and service layers."""

from __future__ import annotations

import re
from datetime import datetime

SYMBOL_PATTERN = re.compile(r"^[A-Z0-9^][A-Z0-9.\-^]{0,19}$")
ALLOWED_STRATEGIES = ("sma", "momentum", "mean_reversion")


def validate_strategy(strategy: str) -> str:
    if not isinstance(strategy, str):
        raise ValueError("Strategy must be a string")
    value = strategy.strip().lower()
    if value not in ALLOWED_STRATEGIES:
        raise ValueError(f"Strategy must be one of {list(ALLOWED_STRATEGIES)}")
    return value


def validate_symbol(symbol: str) -> str:
    """Normalise and validate a market symbol.

    Keeps the accepted character set narrow so symbols can safely be used in
    cache and model artifact paths.
    """
    if not isinstance(symbol, str):
        raise ValueError("Symbol must be a string")
    value = symbol.strip().upper()
    if not value or not SYMBOL_PATTERN.fullmatch(value):
        raise ValueError("Symbol must match ^[A-Z0-9^][A-Z0-9.^-]{0,19}$")
    return value


def parse_int(value, *, name: str, default: int, minimum: int, maximum: int) -> int:
    if value is None or value == "":
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if parsed < minimum or parsed > maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return parsed


def parse_bool(value, *, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    raise ValueError("Expected a boolean value")


def parse_iso_date(value: str | None, *, name: str) -> str | None:
    if value is None or value == "":
        return None
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"{name} must use YYYY-MM-DD format") from exc
    return value
