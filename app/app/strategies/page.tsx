import Link from "next/link";

import { Card } from "@/components/card";
import { DataSourceBadge } from "@/components/data-source-badge";
import { EquityCurve } from "@/components/equity-curve";
import { Nav } from "@/components/nav";
import { StatBlock } from "@/components/stat-block";
import { StatusPill } from "@/components/status-pill";
import { buildEquityCurve, metricsFromCurve } from "@/lib/demo-data";
import { fmtNum, fmtPct } from "@/lib/format";

const CARDS = [
  {
    id: "trend_following",
    title: "trend_following",
    universe: "BTC · ETH · SOL · ARB",
    seed: 11,
    drift: 0.0011,
    vol: 0.011,
    status: "paper" as const,
    blurb: "Time-series momentum with inverse-vol scaling. Long on uptrend strength, short on downtrend, sized inversely to realized vol.",
  },
  {
    id: "stat_arb",
    title: "stat_arb",
    universe: "BTC × ETH",
    seed: 23,
    drift: 0.0007,
    vol: 0.007,
    status: "backtest" as const,
    blurb: "Pair trade on the log-spread. Online OLS for beta; entry at |z| > 2.0, exit at |z| < 0.5. Single-pair scaffold; portfolio composes at the policy layer.",
  },
  {
    id: "vol_target",
    title: "vol_target",
    universe: "BTC · ETH · SOL · AVAX",
    seed: 41,
    drift: 0.0006,
    vol: 0.009,
    status: "stopped" as const,
    blurb: "Long-only inverse-vol targeting 20% annualized portfolio vol. Equal risk-contribution at the single-asset level; renormalised to gross.",
  },
];

export default function StrategiesPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <Nav />
      <main className="flex-1 px-6 py-8">
        <header className="max-w-6xl mx-auto flex items-end justify-between gap-4">
          <div>
            <span className="label">strategies</span>
            <h1 className="mt-2 text-2xl text-text-primary">registered strategy book</h1>
            <p className="mt-2 text-sm text-text-secondary max-w-2xl">
              Each strategy is a pure function: signals → target weights. The meta-policy weights
              them; the risk gate filters every order they emit.
            </p>
          </div>
          <DataSourceBadge source="seeded" />
        </header>

        <section className="max-w-6xl mx-auto mt-8 grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {CARDS.map((c) => {
            const curve = buildEquityCurve(180, 1_000_000, c.drift, c.vol, c.seed);
            const m = metricsFromCurve(curve, 320);
            return (
              <Link key={c.id} href={`/strategies/${c.id}`} className="block group">
                <Card
                  label={c.title}
                  right={<StatusPill status={c.status} />}
                  className="group-hover:border-border-strong transition-colors"
                >
                  <p className="text-xs text-text-tertiary mono mb-3">{c.universe}</p>
                  <EquityCurve data={curve} height={140} showBenchmark={false} showDrawdown={false} />
                  <div className="grid grid-cols-3 gap-3 mt-4">
                    <StatBlock label="SHARPE" value={fmtNum(m.sharpe, 2)} tone="pos" size="sm" />
                    <StatBlock label="MAX DD" value={fmtPct(m.maxDrawdown, 1)} tone="neg" size="sm" />
                    <StatBlock label="DSR" value={fmtNum(m.dsr, 2)} size="sm" />
                  </div>
                  <p className="mt-4 text-sm text-text-secondary leading-relaxed">{c.blurb}</p>
                </Card>
              </Link>
            );
          })}
        </section>
      </main>
    </div>
  );
}
