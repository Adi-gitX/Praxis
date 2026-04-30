"use client";

import { useState } from "react";

import { Card } from "@/components/card";
import { Nav } from "@/components/nav";

const E = Math.E;
const EULER_M = 0.5772156649;

function normalCDF(x: number): number {
  // Abramowitz & Stegun 7.1.26
  const a1 = 0.254829592, a2 = -0.284496736, a3 = 1.421413741;
  const a4 = -1.453152027, a5 = 1.061405429, p = 0.3275911;
  const sign = x < 0 ? -1 : 1;
  const ax = Math.abs(x) / Math.sqrt(2);
  const t = 1 / (1 + p * ax);
  const y = 1 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-ax * ax);
  return 0.5 * (1 + sign * y);
}

function normalPpf(p: number): number {
  // Beasley-Springer / Moro inverse normal CDF
  const a = [-3.969683028665376e1, 2.209460984245205e2, -2.759285104469687e2, 1.383577518672690e2, -3.066479806614716e1, 2.506628277459239];
  const b = [-5.447609879822406e1, 1.615858368580409e2, -1.556989798598866e2, 6.680131188771972e1, -1.328068155288572e1];
  const c = [-7.784894002430293e-3, -3.223964580411365e-1, -2.400758277161838, -2.549732539343734, 4.374664141464968, 2.938163982698783];
  const d = [7.784695709041462e-3, 3.224671290700398e-1, 2.445134137142996, 3.754408661907416];
  const plow = 0.02425;
  const phigh = 1 - plow;
  if (p < plow) {
    const q = Math.sqrt(-2 * Math.log(p));
    return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) /
      ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
  }
  if (p <= phigh) {
    const q = p - 0.5;
    const r = q * q;
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q /
      (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1);
  }
  const q = Math.sqrt(-2 * Math.log(1 - p));
  return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) /
    ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
}

function expectedMaxOfNStandardNormals(n: number): number {
  if (n < 2) return 0;
  return (1 - EULER_M) * normalPpf(1 - 1 / n) + EULER_M * normalPpf(1 - 1 / (n * E));
}

function deflatedSharpeFromInputs(
  observedSharpeAnnual: number,
  nObservations: number,
  nTrials: number,
  varTrials: number = 1,
  skew: number = -0.5,
  excessKurt: number = 4,
  periodsPerYear: number = 365,
): { psr: number; dsr: number; expectedMax: number } {
  const sr = observedSharpeAnnual / Math.sqrt(periodsPerYear); // de-annualize to per-bar
  const denom = (1 - skew * sr + ((excessKurt - 1) / 4) * sr * sr) / (nObservations - 1);
  if (denom <= 0) return { psr: 0, dsr: 0, expectedMax: 0 };
  const se = Math.sqrt(denom);
  if (se === 0) return { psr: 0, dsr: 0, expectedMax: 0 };
  const psr = normalCDF(sr / se);
  const expMax = nTrials >= 2 ? Math.sqrt(varTrials) * expectedMaxOfNStandardNormals(nTrials) : 0;
  const dsr = nTrials >= 2 ? normalCDF((sr - expMax) / se) : psr;
  return { psr, dsr, expectedMax: expMax };
}

export default function MethodologyPage() {
  const [observedSharpe, setObservedSharpe] = useState(1.5);
  const [nTrials, setNTrials] = useState(6);
  const [nObs, setNObs] = useState(365);

  const { psr, dsr, expectedMax } = deflatedSharpeFromInputs(observedSharpe, nObs, nTrials);
  const expMaxAnnual = expectedMax * Math.sqrt(365);

  return (
    <div className="min-h-screen flex flex-col">
      <Nav />
      <main className="flex-1 px-6 py-8 max-w-5xl mx-auto w-full space-y-4">
        <header>
          <span className="label">methodology</span>
          <h1 className="mt-1 text-2xl text-text-primary">deflated sharpe, in one page</h1>
          <p className="mt-2 text-sm text-text-secondary max-w-3xl leading-relaxed">
            Three numbers do most of the work in distinguishing a real edge from a backtest
            artifact: <strong>PSR</strong> (Probabilistic Sharpe), <strong>DSR</strong>
            {" "}(Deflated Sharpe), and the <strong>bootstrap CI</strong>. The first
            corrects classical Sharpe for non-normal returns; the second corrects PSR for
            the number of independent trials you ran; the third tells you how much
            variance the point estimate hides.
          </p>
        </header>

        <Card label="why classical sharpe lies">
          <div className="space-y-3 text-sm text-text-secondary leading-relaxed">
            <p>
              The classical annualized Sharpe ratio <span className="mono text-accent">SR = mean(r) / std(r) · √N</span>
              {" "}is a noisy point estimate. Two failure modes dominate in practice:
            </p>
            <ul className="space-y-2 ml-4 list-disc text-text-secondary marker:text-accent">
              <li>
                <strong>Non-normal returns</strong> bias SR upward when returns are right-skewed
                or fat-tailed. PSR fixes this by computing <span className="mono">P(true SR &gt; 0)</span>
                {" "}directly under a non-normal posterior with skew + kurtosis terms.
              </li>
              <li>
                <strong>Multiple-testing</strong> bias: under the null hypothesis (no edge) and N
                independent trials, the maximum SR over those trials has expected value
                <span className="mono"> E[max] ≈ √var · ((1−γ)·Φ⁻¹(1−1/N) + γ·Φ⁻¹(1−1/(N·e)))</span>
                {" "}(γ = Euler-Mascheroni). DSR shifts the PSR null-benchmark from 0 to that
                expected maximum, so a strategy must beat <em>random search</em> to register.
              </li>
            </ul>
            <p className="text-xs text-text-tertiary">
              References: Bailey & López de Prado, <em>Journal of Risk</em> (2012) for PSR;
              <em> Journal of Portfolio Management</em> (2014) for DSR; Bailey, Borwein,
              López de Prado & Zhu (2017) for PBO.
            </p>
          </div>
        </Card>

        <Card label="interactive — how the deflation penalty grows with N trials">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <Field label="observed annual Sharpe" value={observedSharpe.toFixed(2)}>
              <input
                type="range"
                min={0}
                max={5}
                step={0.05}
                value={observedSharpe}
                onChange={(e) => setObservedSharpe(parseFloat(e.target.value))}
                className="w-full accent-accent"
              />
            </Field>
            <Field label="N trials (independent)" value={String(nTrials)}>
              <input
                type="range"
                min={1}
                max={100}
                step={1}
                value={nTrials}
                onChange={(e) => setNTrials(parseInt(e.target.value))}
                className="w-full accent-accent"
              />
            </Field>
            <Field label="N observations (bars)" value={String(nObs)}>
              <input
                type="range"
                min={60}
                max={5000}
                step={10}
                value={nObs}
                onChange={(e) => setNObs(parseInt(e.target.value))}
                className="w-full accent-accent"
              />
            </Field>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <Result label="PSR (vs SR=0)" value={psr.toFixed(4)} tone={psr > 0.95 ? "pos" : psr > 0.5 ? "neutral" : "neg"} />
            <Result label={`DSR (N=${nTrials})`} value={dsr.toFixed(4)} tone={dsr > 0.95 ? "pos" : dsr > 0.5 ? "neutral" : "neg"} />
            <Result label="E[max SR | null, N]" value={`+${expMaxAnnual.toFixed(2)}`} tone="warn" />
          </div>

          <p className="mt-5 text-xs text-text-tertiary leading-relaxed">
            Key insight: as <span className="mono">N</span> grows, PSR stays flat but DSR
            falls. The same observed Sharpe of <span className="mono">{observedSharpe.toFixed(2)}</span>
            {" "}registers as <span className="mono">PSR = {psr.toFixed(3)}</span> against zero, but
            only <span className="mono">DSR = {dsr.toFixed(3)}</span> against the
            <span className="mono"> N={nTrials}</span> trial null. To accept the alpha you need
            both DSR ≥ 0.95 <em>and</em> a bootstrap CI on Sharpe with lower bound &gt; 0.
          </p>
        </Card>

        <Card label="purged k-fold + embargo (afml ch. 7)">
          <p className="text-sm text-text-secondary leading-relaxed">
            Standard k-fold leaks information when labels are forward-looking windows that
            overlap test fold boundaries. Praxis uses{" "}
            <span className="mono text-accent">PurgedKFold</span> with two safeguards:
          </p>
          <ul className="mt-3 space-y-2 ml-4 list-disc text-sm text-text-secondary marker:text-accent">
            <li>
              <strong>Purging</strong> — drop training rows whose forward-label horizon
              intersects any test row.
            </li>
            <li>
              <strong>Embargo</strong> — drop training rows for an additional buffer
              (default 1% of total samples) <em>after</em> each test fold to kill
              serial-correlation leakage.
            </li>
          </ul>
          <p className="mt-3 text-xs text-text-tertiary">
            Implementation: <code className="mono">agent/src/praxis/backtest/purged_kfold.py</code>{" "}
            — sklearn-compatible <code className="mono">.split()</code> interface.
          </p>
        </Card>

        <Card label="cpcv (afml ch. 12)">
          <p className="text-sm text-text-secondary leading-relaxed">
            Combinatorial Purged CV constructs many backtest paths from a single dataset
            by holding out <span className="mono">n_test_groups</span> of{" "}
            <span className="mono">n_groups</span> at a time. Iterating over all{" "}
            <span className="mono">C(n_groups, n_test_groups)</span> selections produces
            a <em>distribution</em> of OOS Sharpes, from which you can compute the
            <strong> Probability of Backtest Overfit (PBO)</strong> — the fraction of
            in-sample winners that rank below median out-of-sample.
          </p>
          <p className="mt-3 text-xs text-text-tertiary">
            H05 in this repo runs CPCV at <span className="mono">n_groups=6, n_test_groups=2</span>{" "}
            for <strong>15 distinct paths</strong>. The result: mean OOS Sharpe −2.44, all
            15 paths negative — the rejection is robust across backtest constructions, not
            an artifact of one fold split.
          </p>
        </Card>

        <Card label="block bootstrap on sharpe">
          <p className="text-sm text-text-secondary leading-relaxed">
            For confidence intervals, Praxis uses a stationary block bootstrap with block
            length tuned to the autocorrelation of the returns series (e.g.{" "}
            <span className="mono">block=24h</span> for hourly crypto). 10,000 iterations
            gives a 95% CI on Sharpe; if the lower bound crosses zero, the strategy is
            indistinguishable from noise at α=0.05.
          </p>
        </Card>

        <Card label="the three-rule verdict (committed pre-run)">
          <div className="space-y-2 mono text-sm text-text-secondary">
            <p>
              <span className="text-pos">accept</span> iff DSR ≥ threshold <strong>AND</strong> bootstrap-CI lower &gt; 0
            </p>
            <p>
              <span className="text-neg">reject</span> iff Sharpe ≤ 0 <strong>OR</strong> DSR &lt; 0.05
            </p>
            <p>
              <span className="text-warn">inconclusive</span> otherwise
            </p>
          </div>
          <p className="mt-3 text-xs text-text-tertiary leading-relaxed">
            The verdict logic ships in the notebook template, committed before any cell
            runs. This is the pre-registration discipline that makes a clean negative
            result (like H05&apos;s −2.42 Sharpe) more credible than a 100x-cherrypicked positive.
          </p>
        </Card>
      </main>
    </div>
  );
}

function Field({
  label,
  value,
  children,
}: {
  label: string;
  value: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <div className="flex items-baseline justify-between mb-2">
        <span className="label">{label}</span>
        <span className="mono text-text-primary text-sm">{value}</span>
      </div>
      {children}
    </div>
  );
}

function Result({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone: "pos" | "neg" | "warn" | "neutral";
}) {
  const colors = {
    pos: "text-pos",
    neg: "text-neg",
    warn: "text-warn",
    neutral: "text-text-primary",
  } as const;
  return (
    <div className="border border-border-subtle bg-bg-base px-3 py-2">
      <div className="label">{label}</div>
      <div className={`mono text-2xl mt-1 tabular ${colors[tone]}`}>{value}</div>
    </div>
  );
}
