"use client";

import { useMemo, useState } from "react";

import { Card } from "@/components/card";
import { EquityCurve } from "@/components/equity-curve";
import { Nav } from "@/components/nav";
import { ReturnHistogram } from "@/components/return-histogram";
import { StatBlock } from "@/components/stat-block";
import { StatusPill } from "@/components/status-pill";
import { buildEquityCurve, distributionFromCurve, metricsFromCurve } from "@/lib/demo-data";
import { fmtNum, fmtPct } from "@/lib/format";

const STRATEGIES = ["trend_following", "stat_arb", "vol_target"] as const;
const UNIVERSES = ["BTC,ETH,SOL", "BTC,ETH,SOL,AVAX,ARB", "BTC,ETH"] as const;

export default function BacktestPage() {
  const [strategy, setStrategy] = useState<(typeof STRATEGIES)[number]>("trend_following");
  const [universe, setUniverse] = useState<(typeof UNIVERSES)[number]>("BTC,ETH,SOL");
  const [start, setStart] = useState("2024-01-01");
  const [end, setEnd] = useState("2024-12-31");
  const [seed, setSeed] = useState(42);
  const [feeBps, setFeeBps] = useState(5);
  const [maxDD, setMaxDD] = useState(25);
  const [running, setRunning] = useState(false);

  const result = useMemo(() => {
    const days = Math.max(60, Math.round((+new Date(end) - +new Date(start)) / 86_400_000));
    const drift = strategy === "trend_following" ? 0.0011 : strategy === "stat_arb" ? 0.0007 : 0.0006;
    const vol = strategy === "trend_following" ? 0.011 : strategy === "stat_arb" ? 0.007 : 0.009;
    const curve = buildEquityCurve(days, 1_000_000, drift, vol, seed);
    return {
      curve,
      distribution: distributionFromCurve(curve),
      metrics: metricsFromCurve(curve),
    };
  }, [strategy, start, end, seed]);

  function run() {
    setRunning(true);
    setTimeout(() => setRunning(false), 600);
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Nav />
      <main className="flex-1 px-6 py-8">
        <header className="max-w-6xl mx-auto flex items-end justify-between gap-4">
          <div>
            <span className="label">backtest</span>
            <h1 className="mt-1 text-2xl text-text-primary">interactive runner</h1>
          </div>
          <StatusPill status={running ? "backtest" : "stopped"} />
        </header>

        <section className="max-w-6xl mx-auto mt-6 grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-4">
          <Card label="config">
            <div className="space-y-4 text-sm">
              <Field label="strategy">
                <select
                  className="select"
                  value={strategy}
                  onChange={(e) => setStrategy(e.target.value as (typeof STRATEGIES)[number])}
                >
                  {STRATEGIES.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="universe">
                <select
                  className="select"
                  value={universe}
                  onChange={(e) => setUniverse(e.target.value as (typeof UNIVERSES)[number])}
                >
                  {UNIVERSES.map((u) => (
                    <option key={u} value={u}>
                      {u}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="start">
                <input className="input" value={start} onChange={(e) => setStart(e.target.value)} />
              </Field>
              <Field label="end">
                <input className="input" value={end} onChange={(e) => setEnd(e.target.value)} />
              </Field>
              <Field label="seed">
                <input
                  className="input"
                  type="number"
                  value={seed}
                  onChange={(e) => setSeed(Number(e.target.value || 0))}
                />
              </Field>
              <Field label="fee (bps)">
                <input
                  className="input"
                  type="number"
                  value={feeBps}
                  onChange={(e) => setFeeBps(Number(e.target.value || 0))}
                />
              </Field>
              <Field label="max drawdown (%)">
                <input
                  className="input"
                  type="number"
                  value={maxDD}
                  onChange={(e) => setMaxDD(Number(e.target.value || 0))}
                />
              </Field>
              <button
                onClick={run}
                className="w-full px-3 py-2 bg-accent hover:bg-accent-hover text-bg-base mono text-sm"
              >
                {running ? "running…" : "run backtest"}
              </button>
              <p className="text-2xs text-text-tertiary">
                Demo runner: prices are seeded GBM. The Python engine (`praxis backtest`) executes
                the same pipeline against historical data with deterministic seeds.
              </p>
            </div>
          </Card>

          <div className="space-y-4">
            <Card label={`equity · ${strategy} · ${universe}`}>
              <EquityCurve data={result.curve} />
            </Card>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <Card label="SHARPE"><StatBlock label="annualized" value={fmtNum(result.metrics.sharpe, 4)} tone="pos" size="sm" /></Card>
              <Card label="DSR"><StatBlock label="post bias" value={fmtNum(result.metrics.dsr, 4)} size="sm" /></Card>
              <Card label="MAX DD"><StatBlock label="" value={fmtPct(result.metrics.maxDrawdown, 2)} tone="neg" size="sm" /></Card>
              <Card label="HIT"><StatBlock label="daily" value={fmtPct(result.metrics.hitRate, 2)} size="sm" /></Card>
            </div>

            <Card label="return distribution">
              <ReturnHistogram returns={result.distribution} />
            </Card>
          </div>
        </section>
      </main>
      <style>{`
        .select, .input {
          width: 100%;
          background: var(--bg-overlay);
          border: 1px solid var(--border-default);
          padding: 8px 10px;
          color: var(--text-primary);
          font-family: var(--font-geist-mono);
          font-size: 13px;
          outline: none;
        }
        .select:focus, .input:focus {
          border-color: var(--accent);
        }
      `}</style>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="label">{label}</span>
      <div className="mt-1.5">{children}</div>
    </label>
  );
}
