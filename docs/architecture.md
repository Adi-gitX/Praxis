# Praxis Architecture

## Why these layers

The original codebase this fork is built on top of routed an LLM directly to a
wallet. That gives you a chatbot with custody, not a quant agent. Praxis splits
the same problem into the four layers a quant team would actually deploy:

| Layer       | Responsibility                                              | Determinism |
|-------------|-------------------------------------------------------------|-------------|
| Signal      | Compute features from price + on-chain history              | Strict      |
| Strategy    | Map signals → target portfolio weights                      | Strict      |
| Policy      | Pick strategy weights given the regime                      | Optional LLM|
| Risk gate   | Approve / trim / drop every order pre-execution             | Strict      |
| Execution   | Apply slippage + fees, write fills                          | Strict      |

The single non-deterministic seam is the policy layer when an LLM is in the
loop. Everything else is reproducible from a config + a seed.

## Data flow

```
prices  ──►  signals (warm-up cache)
                │
                ▼
         strategies.step(t, prices, signals)
                │           target_weights {asset: w}
                ▼
       meta-policy(regime, signals)
                │           strategy_weights {strategy: w}
                ▼
    combined_target = Σ meta_w · strat_w
                │
                ▼
      orders = delta_to_target(...)
                │
                ▼  for each order:
        risk_gate.check(order, portfolio, marks)
                │  ▼ approved
                │  ▼ trimmed (adjusted_quantity)
                │  ▼ rejected
                ▼
      executor.execute(order, mark, liquidity)
                │
                ▼
        fill → portfolio update
        decision → audit log
```

## Layer-by-layer

### Signals (`agent/src/praxis/signals/`)

Pure functions over `prices: pd.DataFrame`. Each `Signal` exposes a `compute`
method returning the same shape, with a warm-up window of NaNs. Strategies
*never* recompute signals; they read precomputed frames keyed by
`SignalSpec.name`. This means a strategy can declare a 60-bar momentum signal
and a 30-bar vol signal once, and the engine deduplicates them across a
universe.

### Strategies (`agent/src/praxis/strategies/`)

Three reference strategies:

- **TrendFollowing** — log-momentum × inverse-vol, cross-sectional gross-target
  normalisation. Long uptrending, short downtrending, sized inverse to vol.
- **StatArb** — pair trade on the log-spread. Online OLS for beta. Entry at
  |z| ≥ 2.0, exit at |z| ≤ 0.5.
- **VolTarget** — long-only inverse-vol scaling at 20% target portfolio vol.

All three implement `Strategy.step(ts, prices, signals) -> StrategyOutput`.
`StrategyOutput.attribution` lets the policy layer trace which signal
contributed to which weight.

### Policy (`agent/src/praxis/policy/`, `agent/src/praxis/regime/`)

Two implementations, same interface (`MetaPolicy.select`):

- **RuleBasedPolicy** — `Regime → {strategy: weight}` lookup table. The
  baseline. Used in tests and when no `OPENAI_API_KEY` is set.
- **LLMMetaPolicy** — LangGraph state machine that prompts an LLM for strict
  JSON weights. Validates and renormalises. Falls back to rule-based on any
  parsing or runtime error.

Regime detection has two implementations, both implementing
`classify(prices) -> Regime`:

- **VolatilityRegimeDetector** — quantile of recent vol against a long-window
  vol distribution + trend-strength threshold.
- **HMMRegimeDetector** — Gaussian HMM on `(log-return, realized-vol)`,
  Viterbi-decoded. State labels are stable across re-fits because they are
  ranked by realized vol.

### Risk gate (`agent/src/praxis/risk/`)

Single `RiskGate.check(order, portfolio, marks) -> RiskCheck`. Composed of:

- **DrawdownMonitor** — equity high-water mark, one-way trip at
  `max_drawdown`. Once tripped, every order is rejected.
- **ExposureLimits** — per-asset cap, gross cap, net cap. Per-asset breaches
  produce partials (`adjusted_quantity`); gross/net breaches reject.
- **fractional_kelly** — utility called by strategies when sizing positions
  from edge / variance estimates.

The on-chain mirror lives in `contracts/contracts/EmergencyPause.sol`: the
guardian can halt the vault instantly, and unhalting requires the admin to
schedule it and wait `unhaltDelay` seconds before it takes effect.

### Execution (`agent/src/praxis/execution/`)

- **PaperExecutor** — applies slippage (linear-impact: `base + k · size/liquidity`)
  and a flat fee in bps. Writes a `Fill` record per executed order.
- **CDPExecutor** — wraps Coinbase CDP SDK. Disabled by default; raises if
  invoked without credentials. Live execution is opt-in via CLI flag.

### State (`agent/src/praxis/state/`)

- **AuditLog** — append-only JSONL writer. One line per decision. Fast to
  grep, easy to diff between runs.
- **RunRecorder** — per-run directory `runs/<timestamp>_<hash>/` containing
  `config.yaml`, `decisions.jsonl`, `equity_curve.csv`, `trades.csv`,
  `metrics.json`, and (optional) `report.html`.

### Backtest (`agent/src/praxis/backtest/`)

The engine itself is event-driven (one bar at a time, no vectorisation
shortcuts that would be tempting but lookahead-prone). Statistics are factored
out into `stats.py` and `purged_kfold.py` so they can be used independently —
e.g. you can compute DSR on a returns series without ever instantiating the
engine.

## On-chain primitives (`contracts/contracts/`)

| Contract              | Purpose |
|-----------------------|---------|
| `PraxisVault`         | ERC-4626 vault, agent-EOA-callable `agentCall` for routing through approved DEX adapters. Pause + emergency-halt modifiers gate all writes. |
| `StrategyRegistry`    | Whitelisted strategies with per-strategy `maxNotional` and a circuit-breaker bool. The off-chain agent queries `isApproved(id, notional)` pre-trade. |
| `RiskOracle`          | Writer-role-pushed snapshots: drawdown, gross / net leverage, regime enum. Downstream contracts can refuse to interact when stale or breaching. |
| `EmergencyPause`      | Guardian-callable instant halt; admin-callable timelocked unhalt. The vault treats `isHalted()` as a hard freeze on writes. |

The deployment module (`ignition/modules/Praxis.ts`) wires all four together,
parameterised on the base asset, vault name/symbol, and the unhalt delay.

## What's intentionally simple

- The CoinGecko loader caches per-symbol/per-window. No cross-process locks;
  one-shot.
- The HTML report draws inline SVG without matplotlib. No headless-Chrome
  dependency, no plotly bundle, identical render across machines.
- The CDP executor is a stub. The structure is there so the integration
  point is unambiguous; the actual swap path is gated behind credentials and
  a CLI opt-in.
