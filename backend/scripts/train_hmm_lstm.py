"""Standalone training script to run HMM+LSTM trainer from command line.

Usage:
    python scripts/train_hmm_lstm.py --symbol AAPL --epochs 10
"""
from __future__ import annotations

import argparse
from services.models.hmm_lstm_trainer import train_hmm_lstm


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--symbol", required=True)
    p.add_argument("--seq_len", type=int, default=20)
    p.add_argument("--hmm_components", type=int, default=3)
    p.add_argument("--epochs", type=int, default=5)
    p.add_argument("--refresh_pipeline", action="store_true")

    args = p.parse_args()

    print("Starting training for", args.symbol)
    out = train_hmm_lstm(
        args.symbol,
        seq_len=args.seq_len,
        hmm_components=args.hmm_components,
        lstm_epochs=args.epochs,
        refresh_pipeline=args.refresh_pipeline,
    )

    print("Training complete. Artifacts:", out)


if __name__ == "__main__":
    main()
