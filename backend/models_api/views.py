from __future__ import annotations

import logging

from rest_framework.decorators import api_view
from rest_framework.response import Response

from services.auth import authorize_request
from services.callbacks import validate_callback_url
from services.feature_store import get_features
from services.models.registry import registry
from services.utils.helpers import (
    parse_bool,
    parse_int,
    parse_iso_date,
    validate_symbol,
)

logger = logging.getLogger(__name__)


def _celery_available() -> bool:
    try:
        import celery  # noqa: F401
    except ModuleNotFoundError:
        return False
    return True


@api_view(["GET"])
def get_features_view(request):
    try:
        symbol = validate_symbol(request.GET.get("symbol", "AAPL"))
        start = parse_iso_date(request.GET.get("start"), name="start")
        end = parse_iso_date(request.GET.get("end"), name="end")
        refresh = parse_bool(request.GET.get("refresh"), default=False)
        limit = parse_int(
            request.GET.get("limit"),
            name="limit",
            default=200,
            minimum=1,
            maximum=1000,
        )
    except ValueError as exc:
        return Response({"error": str(exc)}, status=400)

    # Cached reads are cheap; refreshing hits a provider and writes to disk.
    if refresh:
        authorize_request(request)

    try:
        df = get_features(symbol, start=start, end=end, refresh=refresh, limit=limit)
        records = df.reset_index().to_dict(orient="records")
        return Response(
            {
                "symbol": symbol,
                "rows": len(records),
                "columns": list(df.columns),
                "data": records,
            }
        )
    except ValueError as exc:
        return Response({"error": str(exc)}, status=400)
    except Exception:
        logger.exception("Feature request failed for %s", symbol)
        return Response({"error": "Unable to load features"}, status=500)


@api_view(["POST"])
def train_model_view(request):
    """Trigger training for a symbol and optionally return the task id."""
    authorize_request(request)
    body = request.data or {}

    try:
        symbol = validate_symbol(body.get("symbol"))
        seq_len = parse_int(body.get("seq_len"), name="seq_len", default=20, minimum=1, maximum=200)
        hmm_components = parse_int(
            body.get("hmm_components"),
            name="hmm_components",
            default=3,
            minimum=2,
            maximum=20,
        )
        lstm_epochs = parse_int(
            body.get("lstm_epochs"),
            name="lstm_epochs",
            default=5,
            minimum=1,
            maximum=100,
        )
        refresh_pipeline = parse_bool(body.get("refresh_pipeline"), default=True)
        wait = parse_bool(body.get("wait"), default=False)
        callback_url = body.get("callback_url")
        callback_secret = body.get("callback_secret")
        if callback_url:
            validate_callback_url(callback_url)
        if callback_secret is not None and not isinstance(callback_secret, str):
            raise ValueError("callback_secret must be a string")
        if callback_secret and len(callback_secret) > 512:
            raise ValueError("callback_secret is too long")
    except ValueError as exc:
        return Response({"error": str(exc)}, status=400)

    if not _celery_available():
        return Response({"error": "Training queue is not configured"}, status=503)

    from services.tasks.train_tasks import train_hmm_lstm_task

    task = train_hmm_lstm_task.apply_async(
        args=(
            symbol,
            seq_len,
            hmm_components,
            lstm_epochs,
            refresh_pipeline,
            callback_url,
            callback_secret,
        )
    )

    if wait:
        try:
            result = task.get(timeout=600)
            return Response({"task_id": task.id, "result": result})
        except Exception:
            logger.exception("Synchronous training failed for %s", symbol)
            return Response({"task_id": task.id, "error": "Training did not complete"}, status=500)

    return Response({"task_id": task.id, "status": "started"})


@api_view(["GET"])
def training_status_view(request, task_id: str):
    authorize_request(request)
    if not _celery_available():
        return Response({"error": "Training queue is not configured"}, status=503)

    from celery.result import AsyncResult
    from core.celery import app as celery_app

    ar = AsyncResult(task_id, app=celery_app)
    out = {"task_id": task_id, "state": ar.state}
    if ar.ready():
        try:
            out["result"] = ar.get()
        except Exception:
            logger.exception("Could not read result for task %s", task_id)
            out["error"] = "Task failed"
    return Response(out)


@api_view(["GET"])
def models_registry_view(request):
    authorize_request(request)
    return Response(registry.list())
