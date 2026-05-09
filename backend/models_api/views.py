from rest_framework.decorators import api_view
from rest_framework.response import Response

from services.feature_store import get_features
from core.celery import app as celery_app
from celery.result import AsyncResult

from services.models.registry import registry
from services.tasks.train_tasks import train_hmm_lstm_task
from services.auth import authorize_request


@api_view(["GET"])
def get_features_view(request):
    symbol = request.GET.get("symbol", "AAPL")
    start = request.GET.get("start")
    end = request.GET.get("end")
    refresh = request.GET.get("refresh", "false").lower() in ("1", "true", "yes")
    limit = request.GET.get("limit")

    try:
        limit = int(limit) if limit is not None else 200
    except Exception:
        limit = 200

    try:
        df = get_features(symbol, start=start, end=end, refresh=refresh, limit=limit)

        # return recent rows as records
        records = df.reset_index().to_dict(orient="records")

        return Response({
            "symbol": symbol,
            "rows": len(records),
            "columns": list(df.columns),
            "data": records,
        })

    except Exception as e:
        return Response({"error": str(e)}, status=400)


@api_view(["POST"])
def train_model_view(request):
    """Trigger training for a symbol. Returns task id or, if `wait=true`, blocks until completion and returns artifacts."""
    # require authentication / API key
    authorize_request(request)
    body = request.data or {}
    symbol = body.get("symbol")
    if not symbol:
        return Response({"error": "symbol is required"}, status=400)

    seq_len = int(body.get("seq_len", 20))
    hmm_components = int(body.get("hmm_components", 3))
    lstm_epochs = int(body.get("lstm_epochs", 5))
    refresh_pipeline = bool(body.get("refresh_pipeline", True))
    wait = str(body.get("wait", "false")).lower() in ("1", "true", "yes")
    callback_url = body.get("callback_url")
    callback_secret = body.get("callback_secret")

    # enqueue task
    task = train_hmm_lstm_task.apply_async(args=(symbol, seq_len, hmm_components, lstm_epochs, refresh_pipeline, callback_url, callback_secret))

    if wait:
        try:
            result = task.get(timeout=600)
            return Response({"task_id": task.id, "result": result})
        except Exception as e:
            return Response({"task_id": task.id, "error": str(e)}, status=500)

    return Response({"task_id": task.id, "status": "started"})


@api_view(["GET"])
def training_status_view(request, task_id: str):
    authorize_request(request)
    ar = AsyncResult(task_id, app=celery_app)
    out = {"task_id": task_id, "state": ar.state}
    if ar.ready():
        try:
            out["result"] = ar.get()
        except Exception as e:
            out["error"] = str(e)
    return Response(out)


@api_view(["GET"])
def models_registry_view(request):
    authorize_request(request)
    return Response(registry.list())
