"""Celery task to invoke HMM-LSTM trainer asynchronously with optional callback."""

from __future__ import annotations

import logging
from typing import Optional

from core.celery import app
from services.callbacks import post_json

logger = logging.getLogger(__name__)


@app.task(bind=True)
def train_hmm_lstm_task(
    self,
    symbol: str,
    seq_len: int = 20,
    hmm_components: int = 3,
    lstm_epochs: int = 5,
    refresh_pipeline: bool = True,
    callback_url: Optional[str] = None,
    callback_secret: Optional[str] = None,
):
    """Train a model and optionally POST the result to an approved callback."""
    try:
        from services.models.hmm_lstm_trainer import train_hmm_lstm

        res = train_hmm_lstm(
            symbol,
            seq_len=seq_len,
            hmm_components=hmm_components,
            lstm_epochs=lstm_epochs,
            refresh_pipeline=refresh_pipeline,
        )
        out = {"status": "ok", "artifacts": res}
    except Exception as exc:
        logger.exception("Training failed for %s", symbol)
        out = {"status": "error", "error": str(exc)}

    if callback_url:
        headers = {"Content-Type": "application/json"}
        if callback_secret:
            headers["X-Callback-Secret"] = callback_secret
        try:
            out["_callback"] = post_json(
                callback_url,
                {"symbol": symbol, "result": out},
                headers=headers,
            )
        except Exception as exc:
            logger.exception("Callback to %s failed", callback_url)
            out["_callback_error"] = str(exc)

    return out
