"""Celery task to invoke HMM-LSTM trainer asynchronously with optional callback."""
from core.celery import app
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def _post_json(url: str, payload: dict, headers: dict | None = None, timeout: int = 10):
    """Post JSON to a callback URL. Tries requests, falls back to urllib."""
    headers = headers or {}
    try:
        import requests

        r = requests.post(url, json=payload, headers=headers, timeout=timeout)
        return {"status": "ok", "http_status": r.status_code, "text": r.text}
    except Exception:
        # fallback to stdlib
        try:
            from urllib.request import Request, urlopen

            req = Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json", **headers})
            resp = urlopen(req, timeout=timeout)
            text = resp.read().decode("utf-8")
            return {"status": "ok", "http_status": resp.getcode(), "text": text}
        except Exception as e:
            return {"status": "error", "error": str(e)}


@app.task(bind=True)
def train_hmm_lstm_task(self, symbol: str, seq_len: int = 20, hmm_components: int = 3, lstm_epochs: int = 5, refresh_pipeline: bool = True, callback_url: Optional[str] = None, callback_secret: Optional[str] = None):
    """Wraps the `train_hmm_lstm` orchestrator and optionally POSTs results to `callback_url`.

    Returns the training result dict and, if attempted, callback metadata under `_callback`.
    """
    try:
        from services.models.hmm_lstm_trainer import train_hmm_lstm

        res = train_hmm_lstm(symbol, seq_len=seq_len, hmm_components=hmm_components, lstm_epochs=lstm_epochs, refresh_pipeline=refresh_pipeline)
        out = {"status": "ok", "artifacts": res}
    except Exception as e:
        logger.exception("Training failed for %s", symbol)
        out = {"status": "error", "error": str(e)}

    # send callback if requested
    if callback_url:
        headers = {"Content-Type": "application/json"}
        if callback_secret:
            headers["X-Callback-Secret"] = callback_secret
        try:
            cb = _post_json(callback_url, {"symbol": symbol, "result": out}, headers=headers)
            out["_callback"] = cb
        except Exception as e:
            logger.exception("Callback to %s failed", callback_url)
            out["_callback_error"] = str(e)

    return out
