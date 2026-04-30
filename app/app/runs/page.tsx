import Link from "next/link";

import { Card } from "@/components/card";
import { Nav } from "@/components/nav";
import { StatBlock } from "@/components/stat-block";
import { StatusPill } from "@/components/status-pill";
import { api, type RunSummary } from "@/lib/api";
import { cn } from "@/lib/utils";
import { fmtNum, fmtPct } from "@/lib/format";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default async function RunsPage() {
  if (!api.isConfigured()) {
    return <NoBackend />;
  }

  let runs: RunSummary[] = [];
  let error: string | null = null;
  try {
    runs = await api.runs();
  } catch (e) {
    error = e instanceof Error ? e.message : "unknown error";
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Nav />
      <main className="flex-1 px-6 py-8 max-w-6xl mx-auto w-full">
        <header className="flex items-end justify-between gap-6">
          <div>
            <span className="label">runs</span>
            <h1 className="mt-1 text-2xl text-text-primary">recorded backtest runs</h1>
            <p className="mt-2 text-sm text-text-secondary max-w-2xl">
              Live data from the FastAPI server at{" "}
              <code className="mono text-accent">{process.env.NEXT_PUBLIC_API_URL}</code>.
              Each row is a directory under{" "}
              <code className="mono">runs/&lt;ts&gt;_&lt;config-hash&gt;/</code>.
            </p>
          </div>
          <StatusPill status={error ? "stopped" : "live"} />
        </header>

        {error ? (
          <Card className="mt-6" label="api error">
            <p className="mono text-sm text-neg">{error}</p>
            <p className="mt-3 text-xs text-text-tertiary">
              Confirm the agent is running:{" "}
              <code className="mono">PRAXIS_RUNS_DIR=../runs poetry run uvicorn praxis.server:app --port 8000</code>
            </p>
          </Card>
        ) : runs.length === 0 ? (
          <Card className="mt-6" label="empty">
            <p className="text-sm text-text-secondary">
              No runs found at <code className="mono">PRAXIS_RUNS_DIR</code>. Generate one:
            </p>
            <pre className="mono text-xs bg-bg-overlay p-3 mt-3 overflow-x-auto">
{`cd agent
poetry run python -m praxis.cli backtest \\
    --config configs/trend_following.yaml \\
    --runs-dir ../runs`}
            </pre>
          </Card>
        ) : (
          <section className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
            {runs.map((r) => (
              <Link key={r.id} href={`/runs/${encodeURIComponent(r.id)}`} className="block group">
                <Card
                  label={r.id}
                  className="group-hover:border-border-strong transition-colors"
                >
                  <div className="grid grid-cols-3 gap-3">
                    <StatBlock
                      label="SHARPE"
                      value={fmtNum(numOr(r.metrics?.sharpe, NaN), 4)}
                      tone={tone(numOr(r.metrics?.sharpe, 0))}
                      size="sm"
                    />
                    <StatBlock
                      label="MAX DD"
                      value={fmtPct(numOr(r.metrics?.max_drawdown, NaN), 2)}
                      tone="neg"
                      size="sm"
                    />
                    <StatBlock
                      label="TOTAL RET"
                      value={fmtPct(numOr(r.metrics?.total_return, NaN), 2)}
                      tone={tone(numOr(r.metrics?.total_return, 0))}
                      size="sm"
                    />
                  </div>
                  <p className={cn("mt-3 text-xs mono text-text-tertiary")}>
                    sortino={fmtNum(numOr(r.metrics?.sortino, NaN), 2)} · calmar=
                    {fmtNum(numOr(r.metrics?.calmar, NaN), 2)} · n_periods=
                    {r.metrics?.n_periods ?? "—"}
                  </p>
                </Card>
              </Link>
            ))}
          </section>
        )}
      </main>
    </div>
  );
}

function NoBackend() {
  return (
    <div className="min-h-screen flex flex-col">
      <Nav />
      <main className="flex-1 px-6 py-8 max-w-3xl mx-auto w-full">
        <header>
          <span className="label">runs</span>
          <h1 className="mt-1 text-2xl text-text-primary">no backend connected</h1>
        </header>
        <Card className="mt-6" label="how to wire this page">
          <p className="text-sm text-text-secondary">
            This page fetches real backtest runs from the praxis-server FastAPI app.
            Set <code className="mono text-accent">NEXT_PUBLIC_API_URL</code> at build time
            (Vercel: project → settings → environment variables; locally: write it to{" "}
            <code className="mono">app/.env.local</code>) and rebuild.
          </p>
          <pre className="mono text-xs bg-bg-overlay p-3 mt-4 overflow-x-auto">
{`# 1 · Run the agent
cd agent
poetry install
PRAXIS_RUNS_DIR=../runs poetry run uvicorn praxis.server:app \\
    --host 0.0.0.0 --port 8000

# 2 · Point the UI at it
echo 'NEXT_PUBLIC_API_URL=http://localhost:8000' > app/.env.local
cd app && npm run dev`}
          </pre>
          <p className="mt-4 text-xs text-text-tertiary">
            One-shot stack:{" "}
            <code className="mono">docker compose up --build</code>{" "}
            (see{" "}
            <Link href="/" className="text-accent hover:text-accent-hover">
              README
            </Link>
            ).
          </p>
        </Card>
      </main>
    </div>
  );
}

function numOr(v: unknown, fallback: number): number {
  return typeof v === "number" && Number.isFinite(v) ? v : fallback;
}

function tone(v: number): "pos" | "neg" | "neutral" {
  if (v > 0) return "pos";
  if (v < 0) return "neg";
  return "neutral";
}
