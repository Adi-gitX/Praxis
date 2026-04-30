import { Card } from "@/components/card";
import { DataSourceBadge } from "@/components/data-source-badge";
import { DataTable, type Column } from "@/components/data-table";
import { EquityCurve } from "@/components/equity-curve";
import { Nav } from "@/components/nav";
import { StatBlock } from "@/components/stat-block";
import { StatusPill } from "@/components/status-pill";
import {
  buildEquityCurve,
  metricsFromCurve,
  recentDecisions,
  snapshotPositions,
  snapshotSignals,
  type DecisionRow,
  type Position,
  type SignalPoint,
} from "@/lib/demo-data";
import { cn } from "@/lib/utils";
import { fmtCompactUSD, fmtNum, fmtPct, fmtSigned, fmtUSD } from "@/lib/format";

export default function TerminalPage() {
  const curve = buildEquityCurve(180, 1_000_000, 0.0011, 0.011, 19);
  const equity = curve[curve.length - 1].equity;
  const metrics = metricsFromCurve(curve);
  const positions = snapshotPositions(equity);
  const signals = snapshotSignals();
  const decisions = recentDecisions();

  const positionCols: Column<Position>[] = [
    { key: "asset", header: "asset", accessor: (r) => <span className="mono">{r.asset}</span> },
    { key: "weight", header: "wgt", align: "right", accessor: (r) => fmtPct(r.weight, 2) },
    { key: "qty", header: "qty", align: "right", accessor: (r) => fmtNum(r.quantity, 4) },
    { key: "avg", header: "avg", align: "right", accessor: (r) => fmtUSD(r.avgPrice) },
    { key: "mark", header: "mark", align: "right", accessor: (r) => fmtUSD(r.mark) },
    {
      key: "pnl",
      header: "p&l",
      align: "right",
      accessor: (r) => (
        <span className={r.pnl >= 0 ? "text-pos" : "text-neg"}>{fmtSigned(r.pnl, 0)}</span>
      ),
    },
    {
      key: "pnlpct",
      header: "%",
      align: "right",
      accessor: (r) => (
        <span className={r.pnl >= 0 ? "text-pos" : "text-neg"}>{fmtPct(r.pnlPct, 2)}</span>
      ),
    },
  ];

  const signalCols: Column<SignalPoint>[] = [
    { key: "name", header: "signal", accessor: (r) => <span className="mono">{r.name}</span> },
    { key: "asset", header: "asset", accessor: (r) => <span className="mono">{r.asset}</span> },
    {
      key: "value",
      header: "value",
      align: "right",
      accessor: (r) => (
        <span className={r.value >= 0 ? "text-pos" : "text-neg"}>{fmtSigned(r.value, 4)}</span>
      ),
    },
    {
      key: "z",
      header: "z",
      align: "right",
      accessor: (r) => {
        const tone = Math.abs(r.zScore) > 2 ? (r.zScore > 0 ? "text-warn" : "text-info") : "text-text-secondary";
        return <span className={tone}>{fmtSigned(r.zScore, 2)}</span>;
      },
    },
  ];

  const decisionCols: Column<DecisionRow>[] = [
    { key: "ts", header: "ts", accessor: (r) => <span className="mono text-text-tertiary">{r.ts}</span> },
    {
      key: "regime",
      header: "regime",
      accessor: (r) => <span className={cn("mono", regimeTone(r.regime))}>{r.regime}</span>,
    },
    { key: "strat", header: "strategy", accessor: (r) => <span className="mono">{r.strategy}</span> },
    { key: "asset", header: "asset", accessor: (r) => <span className="mono">{r.asset}</span> },
    {
      key: "action",
      header: "act",
      accessor: (r) => (
        <span className={r.action === "BUY" ? "text-pos" : r.action === "SELL" ? "text-neg" : "text-text-tertiary"}>
          {r.action}
        </span>
      ),
    },
    { key: "notional", header: "notional", align: "right", accessor: (r) => fmtCompactUSD(r.notional) },
    { key: "reason", header: "reason", accessor: (r) => <span className="text-text-secondary">{r.reason}</span> },
    {
      key: "passed",
      header: "gate",
      accessor: (r) =>
        r.passed ? <span className="text-pos">pass</span> : <span className="text-neg">drop</span>,
    },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      <Nav />
      <main className="flex-1 px-4 py-4 grid grid-rows-[auto_1fr] gap-4">
        <header className="px-2 flex flex-wrap items-end gap-6">
          <div>
            <span className="label">strategy</span>
            <h1 className="mono text-xl text-text-primary mt-1">trend_following · BTC ETH SOL ARB</h1>
          </div>
          <StatBlock label="EQUITY" value={fmtUSD(equity, 0)} tone="neutral" size="sm" />
          <StatBlock
            label="DAILY P&L"
            value={fmtSigned(curve[curve.length - 1].equity - curve[curve.length - 2].equity, 0)}
            tone={curve[curve.length - 1].equity >= curve[curve.length - 2].equity ? "pos" : "neg"}
            size="sm"
          />
          <StatBlock label="SHARPE 30D" value={fmtNum(metrics.sharpe, 4)} tone="pos" size="sm" />
          <StatBlock label="MAX DD" value={fmtPct(metrics.maxDrawdown, 2)} tone="neg" size="sm" />
          <StatBlock label="GROSS" value={fmtPct(0.94, 2)} size="sm" />
          <div className="ml-auto flex items-center gap-2">
            <DataSourceBadge source="seeded" />
            <StatusPill status="paper" />
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-2 grid-rows-[1fr_1fr] gap-4 min-h-0">
          <Card label="EQUITY · 180d · drawdown overlay" className="min-h-[280px]">
            <EquityCurve data={curve} />
          </Card>

          <Card label="POSITIONS · live mark" className="min-h-[280px]" bodyClassName="p-0">
            <DataTable columns={positionCols} rows={positions} rowKey={(r) => r.asset} />
          </Card>

          <Card label="SIGNALS · t = now" className="min-h-[280px]" bodyClassName="p-0">
            <DataTable
              columns={signalCols}
              rows={signals}
              rowKey={(r, i) => `${r.name}-${r.asset}-${i}`}
            />
          </Card>

          <Card
            label="DECISION LOG · last 24"
            className="min-h-[280px]"
            bodyClassName="p-0"
            right={<span className="label">audit · jsonl</span>}
          >
            <DataTable
              columns={decisionCols}
              rows={decisions}
              rowKey={(_, i) => `dec-${i}`}
            />
          </Card>
        </div>
      </main>
    </div>
  );
}

function regimeTone(r: DecisionRow["regime"]): string {
  switch (r) {
    case "trending":
      return "text-pos";
    case "ranging":
      return "text-text-secondary";
    case "high_vol":
      return "text-warn";
    case "crisis":
      return "text-neg";
  }
}
