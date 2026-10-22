import Link from "next/link";

export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col justify-center gap-8 px-6 py-16">
      <p className="font-mono text-sm uppercase tracking-[0.2em] text-zinc-500">
        Quantitative research workspace
      </p>
      <div className="flex max-w-3xl flex-col gap-5">
        <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
          Test a strategy before you trust it.
        </h1>
        <p className="text-lg leading-8 text-zinc-600 dark:text-zinc-400">
          QuantAtlas turns daily market data into transparent, reproducible
          backtests. Compare a strategy with buy-and-hold, inspect drawdowns,
          and keep the assumptions visible.
        </p>
      </div>
      <div className="flex flex-wrap gap-3">
        <Link
          className="rounded-lg bg-black px-5 py-3 text-sm font-semibold text-white transition hover:bg-zinc-800 dark:bg-white dark:text-black dark:hover:bg-zinc-200"
          href="/dashboard"
        >
          Open dashboard
        </Link>
        <a
          className="rounded-lg border border-black/15 px-5 py-3 text-sm font-semibold transition hover:border-black dark:border-white/20 dark:hover:border-white"
          href="https://github.com/matinwgg/QuantAtlas"
          rel="noreferrer"
          target="_blank"
        >
          View source
        </a>
      </div>
      <p className="max-w-2xl text-sm text-zinc-500">
        Research prototype only. Not production trading infrastructure and not
        investment advice.
      </p>
    </main>
  );
}
