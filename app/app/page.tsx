import Link from "next/link";

import { Card } from "@/components/card";
import { EquityCurve } from "@/components/equity-curve";
import { Nav } from "@/components/nav";
import { StatBlock } from "@/components/stat-block";
import { StatusPill } from "@/components/status-pill";
import { Wordmark } from "@/components/wordmark";
import { buildEquityCurve, metricsFromCurve } from "@/lib/demo-data";
import { fmtNum, fmtPct } from "@/lib/format";

export default function LandingPage() {
  const curve = buildEquityCurve(365, 1_000_000, 0.0009, 0.012, 7);
  const metrics = metricsFromCurve(curve);
  return (
    <div className="min-h-screen flex flex-col">
      <Nav />
      <main className="flex-1 px-6 py-12">
        <section className="max-w-5xl mx-auto">
          <Wordmark size="xl" />
          <h1 className="mt-6 text-2xl md:text-3xl text-text-primary leading-tight max-w-3xl">
            A research framework for autonomous quantitative trading on on-chain markets.
          </h1>
          <p className="mt-4 text-md text-text-secondary max-w-3xl leading-relaxed">
            Praxis composes numerical signals, regime-aware meta-policies, and a single risk gate
            into one reproducible pipeline. Strategies are decomposed into signals; the LLM&apos;s
            role is reduced to weighting strategies given the current regime, never to the trade
            itself. Every order passes through Kelly sizing, drawdown circuit-breakers, and
            exposure caps before reaching execution.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Link
              href="/terminal"
              className="inline-flex items-center gap-2 px-4 py-2 bg-accent hover:bg-accent-hover text-bg-base mono text-sm transition-colors"
            >
              launch terminal →
            </Link>
            <Link
              href="/backtest"
              className="inline-flex items-center gap-2 px-4 py-2 border border-border-default hover:border-border-strong text-text-primary mono text-sm transition-colors"
            >
              run backtest
            </Link>
            <Link
              href="/strategies"
              className="inline-flex items-center gap-2 px-4 py-2 text-text-secondary hover:text-text-primary mono text-sm transition-colors"
            >
              strategies →
            </Link>
          </div>
        </section>

        <section className="max-w-5xl mx-auto mt-12 grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card label="HEADLINE SHARPE">
            <StatBlock label="annualized · 365d" value={fmtNum(metrics.sharpe, 4)} tone="pos" />
          </Card>
          <Card label="DEFLATED SHARPE">
            <StatBlock label="post selection-bias" value={fmtNum(metrics.dsr, 4)} tone="neutral" />
          </Card>
          <Card label="MAX DRAWDOWN">
            <StatBlock label="peak-to-trough" value={fmtPct(metrics.maxDrawdown, 2)} tone="neg" />
          </Card>
          <Card label="HIT RATE">
            <StatBlock label="daily" value={fmtPct(metrics.hitRate, 2)} tone="neutral" />
          </Card>
        </section>

        <section className="max-w-5xl mx-auto mt-6">
          <Card
            label="EQUITY · 365d · paper-trade demo"
            right={<StatusPill status="paper" />}
          >
            <EquityCurve data={curve} />
          </Card>
        </section>

        <section className="max-w-5xl mx-auto mt-12 grid md:grid-cols-3 gap-4">
          <Card label="01 · SIGNALS">
            <p className="text-sm text-text-secondary leading-relaxed">
              Momentum, z-score mean-reversion, realized vol, vol-of-vol, cross-asset correlation,
              and on-chain features. Each is a stateless function of the price index — strategies
              compose them, never recompute them.
            </p>
          </Card>
          <Card label="02 · POLICY">
            <p className="text-sm text-text-secondary leading-relaxed">
              A regime detector tags the current state (trending / ranging / high-vol / crisis). A
              LangGraph meta-policy picks strategy weights given the regime; falls back to a
              rule-based table when no LLM key is configured.
            </p>
          </Card>
          <Card label="03 · RISK GATE">
            <p className="text-sm text-text-secondary leading-relaxed">
              Every order is checked by a single chokepoint: drawdown circuit-breaker (one-way
              halt), per-asset exposure cap, gross/net leverage caps. No execution path bypasses
              the gate.
            </p>
          </Card>
        </section>

        <section className="max-w-5xl mx-auto mt-16 text-text-tertiary mono text-2xs">
          <div className="divider pt-6 flex flex-wrap justify-between gap-4">
            <span>praxis · v0.1.0 · MIT</span>
            <span>theory becomes execution</span>
          </div>
        </section>
      </main>
    </div>
  );
}
