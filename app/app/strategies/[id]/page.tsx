import { notFound } from "next/navigation";

import { Card } from "@/components/card";
import { DataTable, type Column } from "@/components/data-table";
import { EquityCurve } from "@/components/equity-curve";
import { Nav } from "@/components/nav";
import { ReturnHistogram } from "@/components/return-histogram";
import { RollingSharpe } from "@/components/rolling-sharpe";
import { StatBlock } from "@/components/stat-block";
import { StatusPill } from "@/components/status-pill";
import {
  buildEquityCurve,
  distributionFromCurve,
  metricsFromCurve,
  rollingSharpe,
} from "@/lib/demo-data";
import { fmtNum, fmtPct } from "@/lib/format";

const STRATEGIES = {
  trend_following: { seed: 11, drift: 0.0011, vol: 0.011, universe: "BTC · ETH · SOL · ARB", status: "paper" as const, params: { lookback: 60, vol_lookback: 30, per_asset_cap: 0.5, gross_target: 1.0 } },
  stat_arb: { seed: 23, drift: 0.0007, vol: 0.007, universe: "BTC × ETH", status: "backtest" as const, params: { lookback: 60, z_entry: 2.0, z_exit: 0.5, target_weight: 0.5 } },
  vol_target: { seed: 41, drift: 0.0006, vol: 0.009, universe: "BTC · ETH · SOL · AVAX", status: "stopped" as const, params: { target_vol: 0.20, vol_lookback: 30, gross: 1.0, per_asset_cap: 0.4 } },
} as const;

type Param = { key: string; value: string };

export default async function StrategyDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const strat = STRATEGIES[id as keyof typeof STRATEGIES];
  if (!strat) notFound();

  const curve = buildEquityCurve(365, 1_000_000, strat.drift, strat.vol, strat.seed);
  const metrics = metricsFromCurve(curve);
  const distribution = distributionFromCurve(curve);
  const rs = rollingSharpe(curve, 30);

  const paramRows: Param[] = Object.entries(strat.params).map(([key, value]) => ({
    key,
    value: typeof value === "number" ? value.toString() : String(value),
  }));
  const paramCols: Column<Param>[] = [
    { key: "key", header: "param", accessor: (r) => <span className="mono">{r.key}</span> },
    { key: "value", header: "value", align: "right", accessor: (r) => <span>{r.value}</span> },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      <Nav />
      <main className="flex-1 px-6 py-8">
        <header className="max-w-6xl mx-auto flex flex-wrap items-end gap-6">
          <div>
            <span className="label">strategy</span>
            <h1 className="mono text-2xl text-text-primary mt-1">{id}</h1>
            <p className="text-xs text-text-tertiary mono mt-1">{strat.universe}</p>
          </div>
          <StatBlock label="SHARPE" value={fmtNum(metrics.sharpe, 4)} tone="pos" size="sm" />
          <StatBlock label="SORTINO" value={fmtNum(metrics.sortino, 4)} tone="pos" size="sm" />
          <StatBlock label="CALMAR" value={fmtNum(metrics.calmar, 4)} size="sm" />
          <StatBlock label="MAX DD" value={fmtPct(metrics.maxDrawdown, 2)} tone="neg" size="sm" />
          <StatBlock label="DSR" value={fmtNum(metrics.dsr, 4)} size="sm" />
          <StatBlock label="HIT RATE" value={fmtPct(metrics.hitRate, 2)} size="sm" />
          <div className="ml-auto"><StatusPill status={strat.status} /></div>
        </header>

        <section className="max-w-6xl mx-auto mt-6 grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Card label="EQUITY CURVE · 365d · benchmark dashed" className="lg:col-span-2">
            <EquityCurve data={curve} height={260} />
          </Card>

          <Card label="ROLLING 30d SHARPE">
            <RollingSharpe data={rs} />
          </Card>

          <Card label="RETURN DISTRIBUTION · daily">
            <ReturnHistogram returns={distribution} />
          </Card>

          <Card label="PARAMETERS" bodyClassName="p-0">
            <DataTable columns={paramCols} rows={paramRows} rowKey={(r) => r.key} />
          </Card>

          <Card label="STATISTICAL TESTS">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="space-y-2">
                <p className="label">deflated sharpe</p>
                <p className="mono tabular text-lg">{fmtNum(metrics.dsr, 4)}</p>
                <p className="text-xs text-text-tertiary">
                  Bailey & López de Prado (2014). Adjusts probabilistic Sharpe for the number of
                  independent trials. Penalty applied for selection-bias under multiple testing.
                </p>
              </div>
              <div className="space-y-2">
                <p className="label">probabilistic sharpe</p>
                <p className="mono tabular text-lg">{fmtNum(metrics.psr, 4)}</p>
                <p className="text-xs text-text-tertiary">
                  Bailey & López de Prado (2012). P(SR &gt; 0) under non-normal returns; corrects
                  classical SR for skew and kurtosis.
                </p>
              </div>
            </div>
          </Card>
        </section>
      </main>
    </div>
  );
}

export async function generateStaticParams() {
  return Object.keys(STRATEGIES).map((id) => ({ id }));
}
