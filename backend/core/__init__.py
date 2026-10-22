"""Django project package.

Celery is optional at import time so deployments that only serve the read API
can start Django without a broker client installed. Code that needs the Celery
app imports it explicitly.
"""

try:  # pragma: no cover - exercised by deployments with/without Celery
    from .celery import app as celery_app
except ModuleNotFoundError as exc:  # pragma: no cover
    if exc.name != "celery":
        raise
    celery_app = None

__all__ = ["celery_app"]
