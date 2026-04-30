import { Card } from "@/components/card";
import { DataSourceBadge } from "@/components/data-source-badge";
import { Nav } from "@/components/nav";
import { StatBlock } from "@/components/stat-block";
import { StatusPill } from "@/components/status-pill";
import { fmtPct } from "@/lib/format";

// Hard-coded snapshot from the H05 notebook output (committed in research/).
// We render this from-record rather than recomputing client-side to match
// what the recruiter sees in the executed notebook exactly.
const REGIME_SUMMARY = {
  asset: "BTCUSDT",
  bars: 17_281,
  range: "2024-05-10 → 2026-04-30",
  states: 2,
  low_vol: { label: "ranging", avg_vol: 0.3223, fraction: 0.62 },
  high_vol: { label: "high_vol", avg_vol: 0.6849, fraction: 0.38 },
  transition: [
    [0.96, 0.04],
    [0.05, 0.95],
  ],
  features: ["log-return (1h)", "realized volatility (24h, annualized)"],
};

const SAMPLE_SEQUENCE: ("low" | "high")[] = (() => {
  // Deterministic visual band: 60% low-vol / 40% high-vol clustered.
  const seq: ("low" | "high")[] = [];
  let mode: "low" | "high" = "low";
  for (let i = 0; i < 60; i++) {
    if (Math.sin(i / 5) > 0.4) mode = "high";
    else if (Math.sin(i / 5) < -0.5) mode = "low";
    seq.push(mode);
  }
  return seq;
})();

export default function RegimePage() {
  return (
    <div className="min-h-screen flex flex-col">
      <Nav />
      <main className="flex-1 px-6 py-8 max-w-6xl mx-auto w-full space-y-4">
        <header className="flex flex-wrap items-end gap-6">
          <div>
            <span className="label">regime</span>
            <h1 className="mt-1 text-2xl text-text-primary">HMM regime detection</h1>
            <p className="mt-2 text-sm text-text-secondary max-w-2xl">
              {REGIME_SUMMARY.states}-state Gaussian HMM (forward-backward + Viterbi)
              fit on {REGIME_SUMMARY.features.join(" + ")} of {REGIME_SUMMARY.asset}.
              States are ranked by realized vol so labels are stable across re-fits.
            </p>
          </div>
          <StatBlock label="BARS" value={REGIME_SUMMARY.bars.toLocaleString()} size="sm" />
          <StatBlock label="RANGE" value={REGIME_SUMMARY.range} size="sm" />
          <StatBlock label="STATES" value={String(REGIME_SUMMARY.states)} size="sm" />
          <div className="ml-auto flex items-center gap-2">
            <DataSourceBadge source="seeded" />
            <StatusPill status="backtest" />
          </div>
        </header>

        <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card label={`state 0 · ${REGIME_SUMMARY.low_vol.label}`}>
            <div className="grid grid-cols-2 gap-4">
              <StatBlock
                label="avg realized vol (annualized)"
                value={fmtPct(REGIME_SUMMARY.low_vol.avg_vol, 2)}
                tone="pos"
              />
              <StatBlock
                label="time in state"
                value={fmtPct(REGIME_SUMMARY.low_vol.fraction, 2)}
              />
            </div>
            <p className="mt-3 text-xs text-text-tertiary leading-relaxed">
              Lower-vol regime — mean realized vol around 32% annualized, characterized
              by mean-reverting price action and lower draw on the momentum sleeve.
              In H05 this regime carries the full position size.
            </p>
          </Card>

          <Card label={`state 1 · ${REGIME_SUMMARY.high_vol.label}`}>
            <div className="grid grid-cols-2 gap-4">
              <StatBlock
                label="avg realized vol (annualized)"
                value={fmtPct(REGIME_SUMMARY.high_vol.avg_vol, 2)}
                tone="neg"
              />
              <StatBlock
                label="time in state"
                value={fmtPct(REGIME_SUMMARY.high_vol.fraction, 2)}
              />
            </div>
            <p className="mt-3 text-xs text-text-tertiary leading-relaxed">
              Higher-vol regime — mean realized vol around 68% annualized. In H05 we
              de-risk to ×0.25 of nominal size in this state. Even with the cut, the
              high-vol regime accounts for the bulk of the strategy bleed (the post-fee
              Sharpe stays negative).
            </p>
          </Card>
        </section>

        <Card label="transition matrix · P(state_{t+1} | state_t)">
          <div className="grid grid-cols-[140px_1fr_1fr] gap-2 text-sm tabular mono items-center">
            <div></div>
            <div className="label text-center">→ ranging</div>
            <div className="label text-center">→ high_vol</div>

            <div className="label">ranging →</div>
            {REGIME_SUMMARY.transition[0].map((p, i) => (
              <div
                key={`r0-${i}`}
                className="text-center px-3 py-2 border border-border-subtle"
                style={{ backgroundColor: `rgba(110, 123, 255, ${p * 0.5})` }}
              >
                {p.toFixed(2)}
              </div>
            ))}

            <div className="label">high_vol →</div>
            {REGIME_SUMMARY.transition[1].map((p, i) => (
              <div
                key={`r1-${i}`}
                className="text-center px-3 py-2 border border-border-subtle"
                style={{ backgroundColor: `rgba(110, 123, 255, ${p * 0.5})` }}
              >
                {p.toFixed(2)}
              </div>
            ))}
          </div>
          <p className="mt-3 text-2xs text-text-tertiary leading-relaxed">
            High self-transition probabilities (0.96 / 0.95) confirm regime
            persistence — once the market enters a state it tends to stay there
            for many bars. This is the property that makes regime-conditional
            sizing meaningful; if transitions were ~0.5 the sizing decision
            would be noise.
          </p>
        </Card>

        <Card label="viterbi-decoded sample band · sketch">
          <div className="flex h-12">
            {SAMPLE_SEQUENCE.map((s, i) => (
              <div
                key={i}
                className="flex-1 border-r border-bg-base"
                style={{
                  backgroundColor: s === "low" ? "rgba(0, 200, 150, 0.55)" : "rgba(255, 92, 92, 0.55)",
                }}
                title={s === "low" ? "ranging" : "high_vol"}
              />
            ))}
          </div>
          <div className="flex justify-between text-2xs text-text-tertiary mt-2 mono">
            <span>past</span>
            <span>now →</span>
          </div>
          <p className="mt-3 text-xs text-text-tertiary leading-relaxed">
            Schematic only — the real decoded sequence (covering 17,281 bars)
            lives in the H05 notebook. Each cell here represents a window; green
            = ranging, red = high_vol. Real Viterbi paths are clustered, not
            alternating, exactly matching the transition-matrix posterior.
          </p>
        </Card>

        <Card label="implementation">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-text-secondary leading-relaxed">
            <div>
              <p className="label mb-2">where</p>
              <ul className="space-y-1 text-xs">
                <li>
                  Code: <code className="mono text-accent">agent/src/praxis/regime/hmm.py</code>
                </li>
                <li>
                  Test: <code className="mono text-accent">agent/tests/test_hmm.py</code>
                </li>
                <li>
                  Used by: <code className="mono text-accent">research/H05_*.ipynb</code>
                </li>
              </ul>
            </div>
            <div>
              <p className="label mb-2">why pure-numpy</p>
              <p className="text-xs text-text-tertiary">
                The EM + Viterbi loop is ~150 LOC and well-cited (Hamilton 1989).
                Avoiding hmmlearn keeps the dependency surface small and lets
                strict-typed mypy cover the regime layer end-to-end. Production
                deployments can swap to <code className="mono">hmmlearn.GaussianHMM</code>
                at the <code className="mono">HMMRegimeDetector.fit_predict</code>
                boundary with no caller changes.
              </p>
            </div>
          </div>
        </Card>
      </main>
    </div>
  );
}
