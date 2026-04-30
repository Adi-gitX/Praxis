# Architecture Decision Records

Lightweight ADR-style log of choices made while building Praxis. Each entry is
the smallest possible explanation that an outside reader can use to challenge
the decision.

## ADR-001 · LLM weights strategies, never trades

**Decision.** The LLM's only job is to map `(regime, signal_summary) →
{strategy: weight}`. Trade generation, sizing, and risk gating are
deterministic.

**Why.** Putting the LLM in the trade-generation path is unauditable, slow,
and brittle. Putting it on the meta-policy layer keeps it where its strength
(soft pattern matching across qualitative regime descriptions) actually
helps, and where its failures are bounded (it can pick a worse mix, but it
cannot mis-size or skip the risk gate).

**Consequences.** The default `RuleBasedPolicy` works without any API keys.
The `LLMMetaPolicy` upgrades the policy layer when keys are present and
falls back to rules on any LLM error.

## ADR-002 · One risk gate, no exceptions

**Decision.** `RiskGate.check` is the only call site at which orders may be
rejected or trimmed. Strategies do not enforce risk locally.

**Why.** Local risk checks decay as the strategy book grows. A strategy that
respects its own per-trade cap of 10% gross exposure can still combine with
two others to produce 30% gross. Centralising the check is the only way to
ensure portfolio-level invariants hold.

**Consequences.** Every order passes through the gate. The gate is shared
state across the run; the drawdown monitor is stateful and the exposure
checks are stateless against the live portfolio.

## ADR-003 · Hardhat over Foundry

**Decision.** Keep Hardhat + Ignition as the contracts toolchain.

**Why.** The original repo had Hardhat wired; the user instruction was
explicit about momentum and seamlessness. Foundry has a meaningfully better
test runner for fuzz/invariant testing, but porting four contracts and the
ignition module is a half-day of churn for a portfolio piece.

**Trade-offs accepted.** No fuzz tests yet. No `forge coverage`. We get the
TypeScript Ignition module and the chai-matcher test runner instead.

## ADR-004 · CoinGecko as the default historical source

**Decision.** Daily close prices via CoinGecko's free API, cached to disk.

**Why.** Zero API key, zero rate-limit ceiling for the volume we run, no
account-creation friction for a reviewer who wants to clone and run.

**Trade-offs accepted.** Daily-close granularity only (we cannot show
intra-day microstructure backtests). CoinGecko occasionally backfills or
revises older points; the cache shields us from that variance once a window
has been pulled. For higher-frequency work, swap in a CCXT loader.

## ADR-005 · Inline-SVG HTML report (no matplotlib)

**Decision.** The single-page HTML report uses inline-SVG drawing primitives
from the standard library + pandas. No matplotlib, no plotly.

**Why.** The report is the reviewer-facing artifact. We want it to render
identically on any machine, with no toolchain divergence, and to be
checked-in friendly (small file, deterministic bytes).

**Consequences.** The chart aesthetic is intentionally minimal: equity curve
+ drawdown band + metrics table. For richer visualisation, the operator
terminal in `app/` is the surface.

## ADR-006 · Drop Nillion entirely

**Decision.** The original codebase used Nillion for encrypted wallet
storage. Praxis ships with vanilla `.env` for CDP credentials.

**Why.** Encrypted secret storage for a single-operator quant prototype is
ceremony, not security. The threat model is "key on operator's laptop" —
addressed by `.env` + filesystem permissions + key rotation. Nillion adds a
multi-node service to provision before anyone can run the project.

**Consequences.** One fewer external dependency to explain in interviews.
Operators using Praxis in production should rotate to a hardware key + KMS,
not Nillion.

## ADR-007 · Pure-numpy HMM, not `hmmlearn`

**Decision.** Implement EM + Viterbi for the regime detector inline.

**Why.** `hmmlearn` is fine but it's another dependency, it transitively
brings scipy.stats, and the regime detector is small enough to be obvious.
The pure implementation is ~150 LOC and well-cited; for production deployments
the same module can be swapped for `hmmlearn.GaussianHMM` with no caller
changes — the public API of `HMMRegimeDetector.fit_predict` is unchanged.

## ADR-008 · Tailwind v3, not v4

**Decision.** Stay on Tailwind v3.4 even though v4 is current.

**Why.** Tailwind v4 moves config to CSS, which would mean rewriting
`tailwind.config.ts` as `@theme` blocks. The aesthetic outcome is identical;
the migration is pure churn for a portfolio piece. We use v3 + CSS vars,
which produces the same token surface.

## ADR-009 · Geist via npm, not local font files

**Decision.** Use `geist/font/sans` and `geist/font/mono` from the `geist`
npm package.

**Why.** Production-grade variable font, free, hosted by the typeface owner
(Vercel). No font-loading flash, automatic preloading via `next/font`. Saves
the ~120kb commit of font files.
