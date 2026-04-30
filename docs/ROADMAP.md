# Roadmap

What's done, what's next, what's deliberately out of scope. Items are
tracked in this file rather than GitHub Issues so the public artifact is
self-contained.

---

## v0.1.0 (shipped)

- Layered architecture: signals → strategies → policy → risk → execution.
- Three reference strategies: trend-following, stat-arb, vol-target.
- Single risk gate: Kelly sizing, drawdown halt, per-asset and aggregate
  exposure caps. No execution path bypasses it.
- Vol-percentile and Gaussian-HMM regime detectors. LangGraph meta-policy
  with a deterministic rule-based fallback.
- Event-driven backtester with deterministic seeding.
- Advanced statistics: Probabilistic Sharpe, Deflated Sharpe (with
  trial-count deflation), 10 000-iter block-bootstrap CIs, PBO from
  CPCV path-Sharpe matrix.
- Purged K-Fold and Combinatorial Purged K-Fold (López de Prado AFML).
- Run recorder: `runs/<ts>_<config-hash>/` with `config.yaml`,
  `decisions.jsonl`, `equity_curve.csv`, `trades.csv`, `metrics.json`,
  inline-SVG `report.html`.
- Two real data loaders: `BinanceDailyLoader` (default, no key required)
  and `CoinGeckoLoader` (requires `COINGECKO_API_KEY` since their 2025
  endpoint change).
- ERC-4626 `PraxisVault` + `StrategyRegistry` + `RiskOracle` +
  `EmergencyPause` (timelocked unhalt). Solc 0.8.27 cancun, OZ v5,
  Hardhat + Ignition, 2/2 tests passing.
- Operator terminal in Next.js 15: landing, terminal (4-quadrant), three
  strategy tearsheets, interactive backtest runner, risk dashboard, vault.
- 4-page LaTeX whitepaper compiled via pandoc + tectonic.
- H05 (HMM volatility regime) executed end-to-end on 17,281 BTCUSDT 1h
  bars, **rejected** under DSR/PSR/bootstrap. Negative result reported
  honestly in the notebook, the whitepaper, and `docs/HYPOTHESES.md`.

## v0.2 (next two weeks of work)

- **Wire the operator terminal to the FastAPI server.** Right now the UI
  renders deterministic seeded demo data; replace with live state from
  `praxis.server`. WebSocket for the streaming decision log, REST for the
  static panels. (`web/src` and `app/lib/api.ts`.)
- **Hyperliquid loader.** A second `BinanceLoader` analogue that pulls
  Hyperliquid's L2 + funding history. Funding-rate basis carry (H06) is
  the first hypothesis that needs it.
- **CCXT live tick stream.** WebSocket-based paper-trade mode reading
  `binance.watch_ohlcv` so the audit log records real-time decisions.
- **CPCV path-Sharpe matrix in the backtest report.** Currently the
  engine supports `walk_forward`; add a `cmd_cpcv` subcommand that emits
  the N-path Sharpe distribution and renders it as a histogram in the
  HTML report.
- **GitHub Actions CI.** The workflow YAML is in `docs/DEPLOY.md`; just
  needs to be committed under `.github/workflows/ci.yml`.

## v0.3 (next month)

- **Flashbots Protect adapter.** A wrapper over
  `eth_sendPrivateTransaction` to `rpc.flashbots.net` for any DEX-side
  execution, with a `dry_run` flag returning the bundle JSON for review.
  H06's MEV-protected variant tests this.
- **Funding-rate basis carry strategy.** Long-spot / short-perp delta
  neutral. Risk: funding flip + basis blowout. The signal already has a
  stub at `agent/src/praxis/signals/onchain.py`.
- **HMM with `hmmlearn` swap-in.** The pure-numpy implementation is fine
  for the demo; for production, swap to `hmmlearn.GaussianHMM` (drop-in
  at the `HMMRegimeDetector.fit_predict` boundary).
- **Per-strategy CDP wallet isolation.** Each strategy gets its own CDP
  server-wallet so a single strategy's blow-up cannot drain the vault.
- **On-chain `RiskOracle` writer cron.** A scheduled job pushes the
  risk-gate's `status()` snapshot to the on-chain `RiskOracle` after each
  rebalance.

## Explicit non-goals

- **A new alpha.** Praxis is a research framework, not an alpha shop.
  Hypotheses go through the deflation pipeline; positive results require
  pre-registration.
- **A multi-tenant SaaS.** No user accounts, no billing, no isolation
  between operators. Single-operator from day one.
- **A new chain.** Praxis targets Base today; Optimism / Arbitrum / Polygon
  are reachable via the same CDP path but not validated.
- **An AGI orchestrator.** The LLM weights strategies. It does not pick
  signals, write code, or send transactions.

## How to propose a change

Open a PR that does *one* thing:

- if it adds a strategy → also add a row in `docs/HYPOTHESES.md` (active
  list) before the run, plus a research notebook with the verdict cell;
- if it adds a signal → add unit tests covering warm-up, NaN propagation,
  and basic statistical sanity;
- if it changes the risk gate → add a negative-path test that verifies
  rejection / partial-fill semantics;
- if it changes the contracts → bump pragma, add a Hardhat test, and
  update `docs/architecture.md` if the layer boundary moves.

Description should answer: what's the hypothesis, what experimental
design pre-registers it, and what would falsify it.
