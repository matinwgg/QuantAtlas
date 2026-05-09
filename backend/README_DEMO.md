Demo: Run Redis + Celery + Django and verify training webhook
============================================================

This document shows the minimal steps to run a demo of the training endpoint and webhook callback.

Prerequisites
- Docker (to run Redis) or a local Redis server
- Python virtualenv with project dependencies installed

Quick commands
--------------

1) Start Redis (Docker):

```bash
docker run -d --name quantatlas-redis -p 6379:6379 redis:7
```

2) Activate your virtualenv and install ML deps if needed:

```bash
# from repo root
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
# optional ML deps for real training
pip install -r requirements-ml.txt || true
```

3) Start the callback receiver in a terminal:

```bash
python backend/scripts/callback_receiver.py --port 9090
```

4) Start a Celery worker (needs Redis running):

```bash
# from backend/ (project root for Django settings)
celery -A core worker --loglevel=info
```

5) Start Django runserver:

```bash
python manage.py runserver 0.0.0.0:8000
```

6) Trigger training (example using curl):

```bash
curl -X POST http://127.0.0.1:8000/api/models/train/ \
  -H 'Content-Type: application/json' \
  -d '{"symbol":"AAPL","seq_len":20,"hmm_components":3,"lstm_epochs":1,"callback_url":"http://127.0.0.1:9090/","wait":false}'
```

If you configured `TRAINING_API_KEYS` or policy, include `X-API-KEY` header.

What to expect
- The training endpoint will enqueue a Celery task and immediately return a `task_id`.
- When the task finishes, the Celery task will POST the result to the callback receiver.

Notes
- This demo uses a lightweight callback receiver and does NOT secure the callback endpoint. In production, validate incoming callbacks and use HTTPS + secrets.
- For long-running training, increase timeouts and consider monitoring/callback retry logic.
