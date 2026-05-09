# Integration Map — QuantAtlas (Phase 1)

This document summarizes the code paths, integration points, and recommended locations for adding new ML models and services (HMM-LSTM, sentiment, LLM agent, RL agent).

## Existing key modules (discovered)

- Data ingestion
  - `backend/services/data/data_loader.py` — fetch_market_data, market detection (`detect_market`), US data via `yfinance`, CSV loader for GSE, `add_returns` helper.
- Strategy implementations
  - `backend/services/strategies/sma.py` — `sma_crossover(df)`
  - `backend/services/strategies/momentum.py` — `momentum_strategy(df)`
  - `backend/services/strategies/mean_reversion.py` — `mean_reversion_strategy(df)`
- Backtesting
  - `backend/services/backtesting/vectorized.py` — `run_vectorized_backtest(df)` plus metrics in `backend/services/backtesting/metrics.py`
  - API endpoint: `backend/backtesting/views.py` exposes `run_backtest` which orchestrates fetch -> strategy -> `run_vectorized_backtest`
- Pipeline helper
  - `backend/services/pipeline.py` — thin orchestration helper (now calls `run_vectorized_backtest`)

## Current data & integration flow

1. REST API `GET /backtesting/run/` (`backend/backtesting/views.py`) receives `symbol` and `strategy`.
2. `fetch_market_data(symbol)` in `backend/services/data/data_loader.py` returns a DataFrame with `close` and `log_return`.
3. Selected strategy function augments the DataFrame with `position` column.
4. `run_vectorized_backtest(df)` computes strategy returns and calls `calculate_metrics` in `metrics.py`.
5. API returns results JSON.

## Immediate fixes applied

- Fixed `backend/services/pipeline.py` to import and call `run_vectorized_backtest` (previously referenced `run_backtest` incorrectly).

## Recommended integration points for new features

- Models and training code
  - Create `backend/services/models/` for model inference code (place `hmm.py`, `lstm.py`, `hmm_lstm_ensemble.py`).
  - Create `scripts/model_train/` or `backend/services/models/train/` for training scripts and notebooks.
  - Save model artifacts to `backend/models/` or `artifacts/models/` with metadata (version, params, timestamp).
- Inference
  - Add `infer()` functions in `backend/services/models/<model>.py` that accept a DataFrame and return `position` (or probabilities/confidence) to match the existing backtest pipeline.
  - Integrate inference in `backend/backtesting/views.py` (add strategy name like `hmm_lstm`) or provide separate endpoints `POST /models/infer/`.
- Feature pipeline
  - Move feature-engineering helpers into `backend/services/features.py` (technical indicators, sentiment merges) so both training and inference share the same transforms.
- Model registry & scheduling
  - Add `backend/services/models/registry.py` to track model versions and metadata.
  - Use Celery or cron jobs for scheduled retraining and data refresh (Celery preferred for scalability).
- LLM & Sentiment
  - Add `backend/services/sentiment/` for connectors and scoring.
  - Add `backend/services/llm_agent/` for prompt templates, wrappers, and aggregation logic.
- RL Agent
  - Add `backend/services/rl/` containing a Gym-like environment that wraps `run_vectorized_backtest` for training.

## API changes to support ML models

- Extend `backend/backtesting/views.py` to accept `strategy=hmm_lstm` or `strategy=model:v1` and call the corresponding inference wrapper.
- Add `POST /models/train/` for kicking off training jobs (authenticated/internal-only).
- Add `GET /models/registry/` to list available models with metadata.

## File-level TODOs (Phase 2 preparatory)

- [ ] Create `backend/services/models/__init__.py` and placeholders for `hmm.py`, `lstm.py`.
- [ ] Create `backend/services/features.py` for shared transforms.
- [ ] Add model artifact path and small registry implementation.
- [ ] Add unit tests for `data_loader` edge-cases (MultiIndex, missing columns).
- [ ] Add validation to `run_vectorized_backtest` to accept probability-based positions (float in [0,1]) and thresholding.

## Notes & Observations

- `data_loader.py` already handles MultiIndex columns from `yfinance` and normalizes columns — good starting point.
- Backtest functions currently expect a `position` column (int) — design inference adapters should return the same shape to minimize changes.
- Keep model outputs compatible with existing `run_vectorized_backtest` by returning `position` (0/1) **and** optional probability/confidence in new columns (`position_prob`, `position_confidence`).

---

Next: implement the shared feature pipeline and create the `backend/services/models` scaffold (Phase 2). If you'd like, I can create the model scaffolding and unit tests now.
