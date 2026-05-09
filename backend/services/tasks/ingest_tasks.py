"""Celery tasks for incremental data ingestion."""
from typing import Iterable

from core.celery import app

from services.data.data_loader import update_raw_data, detect_market


@app.task(bind=True)
def ingest_symbols(self, symbols: Iterable[str]):
    """Update raw cache for a list of symbols.

    This task calls `update_raw_data` for each symbol (US/GSE routing is
    handled by the data loader). It's safe to invoke from Celery Beat.
    """
    updated = 0
    for s in symbols:
        try:
            market = detect_market(s)
            update_raw_data(s, market)
            updated += 1
        except Exception as e:
            # keep going on errors; in prod, replace prints with proper logging
            print(f"Failed to update {s}: {e}")

    return {"updated": updated}


@app.task(bind=True)
def ingest_symbol(self, symbol: str):
    """Single-symbol ingestion convenience task."""
    try:
        market = detect_market(symbol)
        res = update_raw_data(symbol, market)
        return {"symbol": symbol, "rows": 0 if res is None else len(res)}
    except Exception as e:
        return {"symbol": symbol, "error": str(e)}
