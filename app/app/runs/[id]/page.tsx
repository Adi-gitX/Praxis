import Link from "next/link";

import { Card } from "@/components/card";
import { DataTable, type Column } from "@/components/data-table";
import { EquityCurve } from "@/components/equity-curve";
import { Nav } from "@/components/nav";
import { StatBlock } from "@/components/stat-block";
import { StatusPill } from "@/components/status-pill";
import { StreamingDecisions } from "@/components/streaming-decisions";
import { api, type Decision } from "@/lib/api";
import { fmtNum, fmtPct } from "@/lib/format";
import { cn } from "@/lib/utils";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default async function RunDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  if (!api.isConfigured()) {
    return (
      <div className="min-h-screen flex flex-col">
        <Nav />
        <main className="flex-1 px-6 py-8 max-w-3xl mx-auto w-full">
          <span className="label">run</span>
          <h1 className="mt-1 text-2xl text-text-primary">{id}</h1>
          <Card className="mt-6" label="no backend connected">
            <p className="text-sm text-text-secondary">
              Set <code className="mono text-accent">NEXT_PUBLIC_API_URL</code> and rebuild
              to view this run. See{" "}
              <Link href="/runs" className="text-accent hover:text-accent-hover">
                /runs
              </Link>{" "}
              for setup steps.
            </p>
          </Card>
        </main>
      </div>
    );
  }

  let detail: Awaited<ReturnType<typeof api.run>> | null = null;
  let equity: { ts: string; equity: number; benchmark: number; drawdown: number }[] = [];
  let error: string | null = null;
  try {
    detail = await api.run(id);
    const points = await api.equity(id);
    let peak = points[0]?.equity ?? 1;
    equity = points.map((p) => {
      if (p.equity > peak) peak = p.equity;
      return {
        ts: p.ts,
        equity: p.equity,
        benchmark: points[0]?.equity ?? 1,
        drawdown: peak > 0 ? p.equity / peak - 1 : 0,
      };
    });
  } catch (e) {
    error = e instanceof Error ? e.message : "unknown error";
  }

  const m = detail?.metrics ?? {};
  const decisions = detail?.decisions ?? [];

  const cols: Column<Decision>[] = [
    {
      key: "ts",
      header: "ts",
      accessor: (r) => <span className="mono text-text-tertiary">{shortTs(r.ts)}</span>,
    },
    {
      key: "regime",
      header: "regime",
      accessor: (r) => (
        <span className={cn("mono", regimeTone(r.regime))}>{r.regime ?? "—"}</span>
      ),
    },
    {
      key: "weights",
      header: "weights",
      accessor: (r) => (
        <span className="mono text-xs text-text-secondary">
          {r.target_weights ? compactDict(r.target_weights) : "—"}
        </span>
      ),
    },
    {
      key: "notes",
      header: "notes",
      accessor: (r) => <span className="text-xs text-text-tertiary">{(r.notes as string) ?? ""}</span>,
    },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      <Nav />
      <main className="flex-1 px-6 py-8 max-w-6xl mx-auto w-full space-y-4">
        <header className="flex flex-wrap items-end gap-6">
          <div>
            <span className="label">run</span>
            <h1 className="mono text-2xl text-text-primary mt-1">{id}</h1>
            <p className="text-xs text-text-tertiary mono mt-1">
              live · {process.env.NEXT_PUBLIC_API_URL}
            </p>
          </div>
          <StatBlock label="SHARPE" value={fmtNum(asNum(m.sharpe), 4)} tone={tone(asNum(m.sharpe))} size="sm" />
          <StatBlock label="SORTINO" value={fmtNum(asNum(m.sortino), 4)} tone={tone(asNum(m.sortino))} size="sm" />
          <StatBlock label="CALMAR" value={fmtNum(asNum(m.calmar), 4)} size="sm" />
          <StatBlock label="MAX DD" value={fmtPct(asNum(m.max_drawdown), 2)} tone="neg" size="sm" />
          <StatBlock label="TOTAL RET" value={fmtPct(asNum(m.total_return), 2)} tone={tone(asNum(m.total_return))} size="sm" />
          <div className="ml-auto"><StatusPill status={error ? "stopped" : "live"} /></div>
        </header>

        {error ? (
          <Card label="api error">
            <p className="mono text-sm text-neg">{error}</p>
          </Card>
        ) : (
          <>
            <Card label="equity · live">
              {equity.length > 0 ? (
                <EquityCurve data={equity} showBenchmark={false} showDrawdown />
              ) : (
                <p className="text-sm text-text-tertiary">no equity_curve.csv in this run</p>
              )}
            </Card>

            {detail?.config_yaml ? (
              <Card label="config.yaml">
                <pre className="mono text-xs whitespace-pre-wrap text-text-secondary">{detail.config_yaml}</pre>
              </Card>
            ) : null}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <Card label={`decisions · snapshot · ${decisions.length}`} bodyClassName="p-0">
                {decisions.length > 0 ? (
                  <DataTable columns={cols} rows={decisions} rowKey={(_, i) => `d-${i}`} />
                ) : (
                  <p className="p-4 text-sm text-text-tertiary">no decisions.jsonl in this run</p>
                )}
              </Card>

              <Card label="decisions · live stream" bodyClassName="p-0" className="min-h-[320px]">
                <StreamingDecisions runId={id} max={50} />
              </Card>
            </div>
          </>
        )}
      </main>
    </div>
  );
}

function asNum(v: unknown): number {
  return typeof v === "number" && Number.isFinite(v) ? v : NaN;
}

function tone(v: number): "pos" | "neg" | "neutral" {
  if (v > 0) return "pos";
  if (v < 0) return "neg";
  return "neutral";
}

function shortTs(ts?: string): string {
  if (!ts) return "—";
  return ts.length > 19 ? ts.slice(0, 19) : ts;
}

function regimeTone(r?: string): string {
  switch (r) {
    case "trending":
      return "text-pos";
    case "high_vol":
      return "text-warn";
    case "crisis":
      return "text-neg";
    default:
      return "text-text-secondary";
  }
}

function compactDict(d: Record<string, number>): string {
  const parts = Object.entries(d)
    .slice(0, 4)
    .map(([k, v]) => `${k}=${v.toFixed(3)}`);
  return parts.join(" · ");
}
