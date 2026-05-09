"""Celery application for QuantAtlas (Django project).

This module creates a Celery app configured from environment variables.
It defines a minimal setup; customize `app.conf.beat_schedule` to enable
periodic ingestion jobs via Celery Beat.
"""
from __future__ import annotations

import os

from celery import Celery

# set default Django settings module for the 'celery' program
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")

# Broker and result backend can be configured via env vars
app.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
app.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", app.conf.broker_url)
app.conf.timezone = "UTC"

# Example beat schedule (disabled by default). Uncomment and adjust to enable.
# from celery.schedules import crontab
# app.conf.beat_schedule = {
#     'ingest-every-hour': {
#         'task': 'services.tasks.ingest_symbols',
#         'schedule': crontab(minute=0, hour='*/1'),
#         'args': (['AAPL', 'BTC-USD'],),
#     },
# }

# Autodiscover tasks in the services.tasks module
app.autodiscover_tasks(["services.tasks"])
