# QuantAtlas

QuantAtlas is a quantitative-finance research prototype for processing market
data, computing indicators, fitting research models, and running transparent
long-only backtests. It is a research tool, **not** production trading
infrastructure or investment advice.

## What works

- Django REST API with a vectorized daily backtest (`SMA`, `momentum`,
  `mean-reversion`)
- Metrics: total and annual return, volatility, Sharpe ratio, max drawdown,
  turnover, trades, buy-and-hold comparison
- Cached feature store with validated symbol paths and JSON transformation
  pipelines
- Optional HMM/LSTM training queue (Celery + Redis)
- Next.js dashboard for running a backtest and inspecting metrics
- Docker Compose stack: Django, Celery worker, Redis, Next.js, nginx

## Project structure

```text
.
├── backend/                  # Django apps, services, tests
├── frontend/quant-atlas-webapp/  # Next.js dashboard
├── infrastructure/           # Dockerfiles and nginx config
├── data/                     # Small local market-data fixtures
├── models/                   # Model artifacts
├── docker-compose.yml
└── requirements.txt          # Canonical Python dependency set
```

## Local development

Prerequisites: Python 3.11 or 3.12, Node 22, and (optionally) Redis.

### Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp backend/.env.example .env
# Export the variables from .env (or use your process manager).
export DJANGO_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
export DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
export TRAINING_API_KEYS="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"

cd backend
python manage.py migrate
python manage.py runserver
```

The API is at `http://localhost:8000`.

### Frontend

```bash
cd frontend/quant-atlas-webapp
cp .env.example .env.local
npm ci
npm run dev
```

Open `http://localhost:3000/dashboard`.

### Tests and checks

```bash
pytest                                   # service tests
cd backend
python manage.py test backtesting         # Django API tests
bandit -r . -x data -ll                   # medium+ findings
python manage.py check --deploy
```

Set `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, and
`DJANGO_SECURE_SSL_REDIRECT=false` when running the Django test suite locally.

## API

```text
GET  /api/backtest/run/?symbol=AAPL&strategy=sma
GET  /api/features/get/?symbol=AAPL&limit=200
POST /api/models/train/          # requires X-API-KEY or staff login
GET  /api/models/train/<task_id>/ # requires X-API-KEY or staff login
GET  /api/models/registry/       # requires X-API-KEY or staff login
```

`/api/features/get/` allows anonymous cached reads but requires an API key when
`refresh=true`, because refreshing calls an upstream provider and writes to
disk. Read endpoints are rate-limited. Training parameters, symbols, dates, and
limits are validated server-side.

## Docker Compose

```bash
cp .env.example .env
# Set DJANGO_SECRET_KEY and TRAINING_API_KEYS in .env.
docker compose up --build
```

Open `http://localhost:8080`. The local stack serves HTTP on port 8080. For a
real deployment, terminate TLS at the edge, set
`DJANGO_SECURE_SSL_REDIRECT=true`, and use a managed PostgreSQL/Redis service
rather than the local SQLite volume.

## Methodology and limitations

- Positions are long-only and aligned to the return they earn; strategy helpers
  shift signals by one day to avoid look-ahead.
- Returns are daily log returns. The Sharpe ratio uses daily simple excess
  returns annualized with 252 trading days; the risk-free rate defaults to zero.
- Transaction costs, slippage, taxes, borrow costs, and market impact are not
  modelled. Turnover is reported so these costs can be estimated separately.
- The HMM/LSTM training pipeline is research code. It is not validated for live
  trading, and model artifacts must be treated as trusted server-side data.
- Do not load user-supplied pickle or PyTorch artifacts. HMM artifacts are
  loaded only from the application's model directory; PyTorch checkpoints use
  `weights_only=True`.
- Backtests are in-sample unless the caller supplies a genuinely out-of-sample
  dataset. Walk-forward validation and experiment tracking remain future work.

## Security notes

- Secrets come from environment variables; Django refuses to start without
  `DJANGO_SECRET_KEY`.
- Production mode sets secure cookies, HSTS, HTTPS redirect, and
  content-type/referrer protections.
- CORS and CSRF origins are explicit allow-lists.
- Training callbacks are validated to prevent SSRF: public HTTPS only in
  production, no credentials in URLs, no redirects, and a short timeout.
- Symbol input is restricted to a safe character set before it is used in cache
  or model paths.

## License

MIT. See `LICENSE`.
