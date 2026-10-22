"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

import { api, getApiError } from "@/lib/api";

type Metrics = {
  total_return: number;
  buy_hold_return: number;
  annual_return: number;
  annual_volatility: number;
  sharpe: number;
  max_drawdown: number;
  turnover: number;
  trades: number;
  observations: number;
  start: string;
  end: string;
};

type EquityPoint = {
  date: string;
  strategy: number;
  buyhold: number;
};

type BacktestResponse = {
  symbol: string;
  strategy: string;
  results: {
    metrics: Metrics;
    equity_curve: EquityPoint[];
  };
};

const STRATEGIES = [
  { value: "sma", label: "SMA crossover (20/50)" },
  { value: "momentum", label: "Momentum (20 day)" },
  { value: "mean_reversion", label: "Mean reversion (20 day)" },
];

function formatPercent(value: number) {
  return `${(value * 100).toFixed(2)}%`;
}

function formatNumber(value: number, digits = 2) {
  return Number.isFinite(value) ? value.toFixed(digits) : "—";
}

export default function DashboardPage() {
  const [symbol, setSymbol] = useState("AAPL");
  const [strategy, setStrategy] = useState("sma");
  const [result, setResult] = useState<BacktestResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function runBacktest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await api.get<BacktestResponse>("/api/backtest/run/", {
        params: { symbol: symbol.trim().toUpperCase(), strategy },
      });
      setResult(response.data);
    } catch (requestError) {
      setError(getApiError(requestError));
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  const metrics = result?.results.metrics;
  const recentCurve = result?.results.equity_curve.slice(-5).reverse() ?? [];

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-8 px-6 py-12">
      <header className="flex flex-col gap-3 border-b border-black/10 pb-6 dark:border-white/10">
        <Link className="text-sm text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100" href="/">
          ← QuantAtlas
        </Link>
        <h1 className="text-3xl font-semibold tracking-tight">Backtest dashboard</h1>
        <p className="max-w-2xl text-zinc-600 dark:text-zinc-400">
          Run a long-only daily strategy on cached or live market data. Results are
          research output, not investment advice.
        </p>
      </header>

      <form
        className="grid gap-4 rounded-xl border border-black/10 bg-white p-5 shadow-sm sm:grid-cols-[1fr_1fr_auto] dark:border-white/10 dark:bg-zinc-950"
        onSubmit={runBacktest}
      >
        <label className="flex flex-col gap-1 text-sm font-medium">
          Symbol
          <input
            className="rounded-lg border border-black/15 bg-transparent px-3 py-2 font-mono uppercase outline-none focus:border-black dark:border-white/20 dark:focus:border-white"
            maxLength={20}
            onChange={(event) => setSymbol(event.target.value)}
            placeholder="AAPL"
            required
            value={symbol}
          />
        </label>

        <label className="flex flex-col gap-1 text-sm font-medium">
          Strategy
          <select
            className="rounded-lg border border-black/15 bg-transparent px-3 py-2 outline-none focus:border-black dark:border-white/20 dark:focus:border-white"
            onChange={(event) => setStrategy(event.target.value)}
            value={strategy}
          >
            {STRATEGIES.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </label>

        <button
          className="self-end rounded-lg bg-black px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-white dark:text-black dark:hover:bg-zinc-200"
          disabled={loading}
          type="submit"
        >
          {loading ? "Running…" : "Run backtest"}
        </button>
      </form>

      <div aria-live="polite" className="min-h-6 text-sm">
        {error ? <p className="text-red-600 dark:text-red-400">{error}</p> : null}
      </div>

      {metrics ? (
        <section className="flex flex-col gap-6">
          <div className="flex flex-wrap items-baseline justify-between gap-3">
            <h2 className="text-xl font-semibold">
              {result?.symbol} · {result?.strategy}
            </h2>
            <p className="text-sm text-zinc-500">
              {metrics.start} → {metrics.end} · {metrics.observations} observations
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              ["Total return", formatPercent(metrics.total_return)],
              ["Buy & hold", formatPercent(metrics.buy_hold_return)],
              ["Annual return", formatPercent(metrics.annual_return)],
              ["Annual volatility", formatPercent(metrics.annual_volatility)],
              ["Sharpe", formatNumber(metrics.sharpe)],
              ["Max drawdown", formatPercent(metrics.max_drawdown)],
              ["Turnover", formatNumber(metrics.turnover)],
              ["Trades", String(metrics.trades)],
            ].map(([label, value]) => (
              <div
                className="rounded-xl border border-black/10 bg-white p-4 dark:border-white/10 dark:bg-zinc-950"
                key={label}
              >
                <p className="text-xs uppercase tracking-wide text-zinc-500">{label}</p>
                <p className="mt-1 text-2xl font-semibold tabular-nums">{value}</p>
              </div>
            ))}
          </div>

          <div className="overflow-hidden rounded-xl border border-black/10 dark:border-white/10">
            <table className="w-full text-left text-sm">
              <thead className="bg-zinc-50 text-zinc-500 dark:bg-zinc-900">
                <tr>
                  <th className="px-4 py-3 font-medium">Date</th>
                  <th className="px-4 py-3 text-right font-medium">Strategy</th>
                  <th className="px-4 py-3 text-right font-medium">Buy & hold</th>
                </tr>
              </thead>
              <tbody>
                {recentCurve.map((point) => (
                  <tr className="border-t border-black/5 dark:border-white/5" key={point.date}>
                    <td className="px-4 py-2 font-mono text-xs">{point.date.slice(0, 10)}</td>
                    <td className="px-4 py-2 text-right tabular-nums">{point.strategy.toFixed(4)}</td>
                    <td className="px-4 py-2 text-right tabular-nums">{point.buyhold.toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}
    </main>
  );
}
