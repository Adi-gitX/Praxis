import { Card } from "@/components/card";
import { DataTable, type Column } from "@/components/data-table";
import { EquityCurve } from "@/components/equity-curve";
import { Nav } from "@/components/nav";
import { StatBlock } from "@/components/stat-block";
import { StatusPill } from "@/components/status-pill";
import { buildEquityCurve, snapshotPositions, type Position } from "@/lib/demo-data";
import { cn } from "@/lib/utils";
import { fmtNum, fmtPct, fmtUSD } from "@/lib/format";

const ASSETS = ["BTC", "ETH", "SOL", "ARB"];

function correlationMatrix(): number[][] {
  // Hand-tuned demo correlations consistent with crypto majors clustering.
  return [
    [1.00, 0.78, 0.65, 0.59],
    [0.78, 1.00, 0.71, 0.68],
    [0.65, 0.71, 1.00, 0.62],
    [0.59, 0.68, 0.62, 1.00],
  ];
}

export default function RiskPage() {
  const curve = buildEquityCurve(180, 1_000_000, 0.0009, 0.012, 33);
  const equity = curve[curve.length - 1].equity;
  const positions = snapshotPositions(equity);
  const gross = positions.reduce((a, p) => a + Math.abs(p.weight), 0);
  const net = positions.reduce((a, p) => a + p.weight, 0);
  const matrix = correlationMatrix();

  const peak = curve.reduce((a, p) => Math.max(a, p.equity), 0);
  const dd = (peak - equity) / peak;
  const ddCap = 0.25;
  const ddDist = ddCap - dd;

  const cols: Column<Position>[] = [
    { key: "asset", header: "asset", accessor: (r) => <span className="mono">{r.asset}</span> },
    { key: "weight", header: "wgt", align: "right", accessor: (r) => fmtPct(r.weight, 2) },
    { key: "notional", header: "notional", align: "right", accessor: (r) => fmtUSD(r.weight * equity, 0) },
    { key: "var", header: "var(95%)", align: "right", accessor: (r) => fmtUSD(r.weight * equity * 0.04, 0) },
    {
      key: "cap",
      header: "cap",
      align: "right",
      accessor: (r) => (
        <span className={r.weight > 0.30 ? "text-warn" : "text-text-secondary"}>30.00%</span>
      ),
    },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      <Nav />
      <main className="flex-1 px-6 py-8 max-w-6xl mx-auto w-full space-y-4">
        <header className="flex flex-wrap items-end gap-6">
          <div>
            <span className="label">risk dashboard</span>
            <h1 className="mt-1 text-2xl text-text-primary">portfolio risk posture</h1>
          </div>
          <StatBlock label="DRAWDOWN" value={fmtPct(dd, 2)} tone={dd > 0.15 ? "warn" : "neutral"} size="sm" />
          <StatBlock label="DD CAP" value={fmtPct(ddCap, 2)} tone="neg" size="sm" />
          <StatBlock label="DISTANCE" value={fmtPct(ddDist, 2)} tone={ddDist < 0.05 ? "warn" : "pos"} size="sm" />
          <StatBlock label="GROSS" value={fmtPct(gross, 2)} size="sm" />
          <StatBlock label="NET" value={fmtPct(net, 2)} size="sm" />
          <StatBlock label="VAR(95%) 1d" value={fmtUSD(equity * 0.026, 0)} tone="neg" size="sm" />
          <div className="ml-auto"><StatusPill status="paper" /></div>
        </header>

        <Card label="EQUITY CURVE · drawdown distance to circuit-breaker">
          <EquityCurve data={curve} height={240} />
        </Card>

        <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Card label="EXPOSURE · per-asset · 30% cap" bodyClassName="p-0">
            <DataTable columns={cols} rows={positions} rowKey={(r) => r.asset} />
          </Card>

          <Card label="CORRELATION · 60d rolling">
            <table className="w-full text-sm tabular mono">
              <thead>
                <tr>
                  <th></th>
                  {ASSETS.map((a) => (
                    <th key={a} className="px-2 py-2 label text-right">{a}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {matrix.map((row, i) => (
                  <tr key={ASSETS[i]} className="border-t border-border-subtle">
                    <td className="px-2 py-2 label">{ASSETS[i]}</td>
                    {row.map((v, j) => {
                      const tint = Math.max(0, Math.min(1, (v - 0.4) / 0.6));
                      const bg = `rgba(110, 123, 255, ${tint * 0.45})`;
                      return (
                        <td key={j} className="px-2 py-2 text-right" style={{ backgroundColor: bg }}>
                          <span className={cn(v > 0.7 ? "text-warn" : "text-text-primary")}>
                            {fmtNum(v, 2)}
                          </span>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="mt-3 text-2xs text-text-tertiary leading-relaxed">
              High intra-cluster correlation (BTC-ETH 0.78) is the dominant risk concentration in
              crypto majors. Diversification benefit is bounded; gross-exposure cap matters more
              than asset-count.
            </p>
          </Card>
        </section>

        <Card label="RISK GATE · last 100 orders">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Stat label="passed" value="92" tone="pos" />
            <Stat label="trimmed" value="6" tone="warn" />
            <Stat label="dropped · per-asset" value="1" tone="neg" />
            <Stat label="dropped · drawdown" value="1" tone="neg" />
          </div>
          <p className="mt-4 text-xs text-text-tertiary leading-relaxed">
            Every order passes through `RiskGate.check`. The drawdown monitor is a one-way halt;
            the exposure check produces partials when an order would breach a per-asset, gross,
            or net cap. There is no execution path that bypasses this layer.
          </p>
        </Card>
      </main>
    </div>
  );
}

function Stat({ label, value, tone }: { label: string; value: string; tone: "pos" | "neg" | "warn" | "neutral" }) {
  const colors = {
    pos: "text-pos",
    neg: "text-neg",
    warn: "text-warn",
    neutral: "text-text-primary",
  } as const;
  return (
    <div>
      <span className="label">{label}</span>
      <p className={cn("mono text-2xl mt-1 tabular", colors[tone])}>{value}</p>
    </div>
  );
}
