# Repo Guide — Where Everything Lives

Use this index when you need to find a specific concept fast. The README is the
narrative; this is the lookup table.

---

## I want to read…

| Topic | File |
|---|---|
| Five-minute pitch | [`README.md`](../README.md) |
| The actual paper | [`docs/WHITEPAPER.pdf`](./WHITEPAPER.pdf) |
| Layer-by-layer architecture rationale | [`docs/architecture.md`](./architecture.md) |
| All the architectural decisions and *why* | [`docs/DECISIONS.md`](./DECISIONS.md) |
| Pre-registered hypotheses and their verdicts | [`docs/HYPOTHESES.md`](./HYPOTHESES.md) |
| The H05 hypothesis tearsheet (no inputs) | [`docs/tearsheets/H05.html`](./tearsheets/H05.html) |
| The executed H05 notebook (with inputs) | [`research/H05_hmm_volatility_regime.ipynb`](../research/H05_hmm_volatility_regime.ipynb) |
| Roadmap (v0.1 / v0.2 / v0.3 / non-goals) | [`docs/ROADMAP.md`](./ROADMAP.md) |
| Deploy to GitHub + Vercel + Base Sepolia | [`docs/DEPLOY.md`](./DEPLOY.md) |
| Reproducibility recipe | [`REPRODUCE.md`](../REPRODUCE.md) |

## I want to find…

| Concept | Where |
|---|---|
| `Signal` ABC | [`agent/src/praxis/signals/base.py`](../agent/src/praxis/signals/base.py) |
| Momentum / z-score / vol / correlation / on-chain | [`agent/src/praxis/signals/`](../agent/src/praxis/signals) |
| `Strategy` ABC + 3 strategies | [`agent/src/praxis/strategies/`](../agent/src/praxis/strategies) |
| Risk gate (Kelly + drawdown + exposure) | [`agent/src/praxis/risk/`](../agent/src/praxis/risk) |
| LangGraph LLM meta-policy + rule-based fallback | [`agent/src/praxis/policy/meta_policy.py`](../agent/src/praxis/policy/meta_policy.py) |
| Vol-percentile regime classifier | [`agent/src/praxis/policy/regime_detector.py`](../agent/src/praxis/policy/regime_detector.py) |
| Pure-numpy Gaussian HMM (EM + Viterbi) | [`agent/src/praxis/regime/hmm.py`](../agent/src/praxis/regime/hmm.py) |
| Event-driven backtester loop | [`agent/src/praxis/backtest/engine.py`](../agent/src/praxis/backtest/engine.py) |
| PSR / DSR / bootstrap CI / PBO | [`agent/src/praxis/backtest/stats.py`](../agent/src/praxis/backtest/stats.py) |
| Purged K-Fold + CPCV | [`agent/src/praxis/backtest/purged_kfold.py`](../agent/src/praxis/backtest/purged_kfold.py) |
| HTML tearsheet renderer | [`agent/src/praxis/backtest/report.py`](../agent/src/praxis/backtest/report.py) |
| JSONL audit log + run recorder | [`agent/src/praxis/state/`](../agent/src/praxis/state) |
| Paper executor (default) | [`agent/src/praxis/execution/cdp_executor.py`](../agent/src/praxis/execution/cdp_executor.py) |
| Linear-impact slippage model | [`agent/src/praxis/execution/slippage.py`](../agent/src/praxis/execution/slippage.py) |
| ccxt Binance loader (parquet cached) | [`agent/src/praxis/data/ccxt_binance.py`](../agent/src/praxis/data/ccxt_binance.py) |
| `BinanceDailyLoader` / `CoinGeckoLoader` for the CLI | [`agent/src/praxis/backtest/data_loader.py`](../agent/src/praxis/backtest/data_loader.py) |
| `praxis backtest` / `paper-trade` / `strategies` CLI | [`agent/src/praxis/cli.py`](../agent/src/praxis/cli.py) |
| Strategy YAML configs | [`agent/configs/`](../agent/configs) |
| All Python tests | [`agent/tests/`](../agent/tests) |
| `PraxisVault.sol` (ERC-4626) | [`contracts/contracts/Vault.sol`](../contracts/contracts/Vault.sol) |
| `StrategyRegistry.sol` (whitelist + breakers) | [`contracts/contracts/StrategyRegistry.sol`](../contracts/contracts/StrategyRegistry.sol) |
| `RiskOracle.sol` (writer-role snapshots) | [`contracts/contracts/RiskOracle.sol`](../contracts/contracts/RiskOracle.sol) |
| `EmergencyPause.sol` (timelocked unhalt) | [`contracts/contracts/EmergencyPause.sol`](../contracts/contracts/EmergencyPause.sol) |
| Hardhat Ignition deploy module | [`contracts/ignition/modules/Praxis.ts`](../contracts/ignition/modules/Praxis.ts) |
| Hardhat tests | [`contracts/test/Vault.test.ts`](../contracts/test/Vault.test.ts) |
| Operator terminal landing page | [`app/app/page.tsx`](../app/app/page.tsx) |
| 4-quadrant trading canvas | [`app/app/terminal/page.tsx`](../app/app/terminal/page.tsx) |
| Strategy tearsheet (per-strategy detail) | [`app/app/strategies/[id]/page.tsx`](../app/app/strategies/[id]/page.tsx) |
| Interactive backtest runner | [`app/app/backtest/page.tsx`](../app/app/backtest/page.tsx) |
| Risk dashboard | [`app/app/risk/page.tsx`](../app/app/risk/page.tsx) |
| ERC-4626 deposit/withdraw shell | [`app/app/vault/page.tsx`](../app/app/vault/page.tsx) |
| OG image (1200×630, edge runtime) | [`app/app/opengraph-image.tsx`](../app/app/opengraph-image.tsx) |
| Vercel production config | [`app/vercel.json`](../app/vercel.json) |
| Equity curve chart component | [`app/components/equity-curve.tsx`](../app/components/equity-curve.tsx) |
| Status pill / stat block / data table | [`app/components/`](../app/components) |
| Seeded demo data | [`app/lib/demo-data.ts`](../app/lib/demo-data.ts) |
| Number formatting helpers | [`app/lib/format.ts`](../app/lib/format.ts) |
| LaTeX whitepaper source | [`whitepaper/main.md`](../whitepaper/main.md) |
| BibTeX references | [`whitepaper/refs.bib`](../whitepaper/refs.bib) |

## I want to run…

| Goal | Command (from repo root) |
|---|---|
| The operator terminal | `cd app && npm install && npm run dev` |
| The Python test suite | `cd agent && poetry install && poetry run pytest -q` |
| Strict type-check | `cd agent && poetry run mypy --strict src/praxis` |
| Lint | `cd agent && poetry run ruff check .` |
| A real-data backtest | `cd agent && poetry run python -m praxis.cli backtest --config configs/trend_following.yaml --runs-dir ../runs` |
| The H05 notebook end-to-end | `cd agent && poetry run jupyter nbconvert --execute --to notebook --inplace ../research/H05_hmm_volatility_regime.ipynb` |
| Hardhat compile | `cd contracts && npx hardhat compile` |
| Hardhat tests | `cd contracts && WALLET_KEY=0x...01 npx hardhat test` |
| The whitepaper PDF (rebuild) | `pandoc whitepaper/main.md -o docs/WHITEPAPER.pdf --pdf-engine=tectonic --citeproc` |
| List available strategies | `cd agent && poetry run python -m praxis.cli strategies` |

## I want to extend…

| Add | Steps |
|---|---|
| A new signal | implement `Signal` in `agent/src/praxis/signals/`; add unit tests for warm-up, NaN propagation, sanity |
| A new strategy | implement `Strategy` in `agent/src/praxis/strategies/`; register in `strategies/__init__.py:REGISTRY`; add a YAML config |
| A new regime detector | implement `classify(prices) -> Regime` in `agent/src/praxis/regime/`; register name in `policy/meta_policy.RuleBasedPolicy.table` |
| A new risk check | add the check to `agent/src/praxis/risk/gate.py:RiskGate.check`; cover the *negative path* in tests |
| A new data source | mirror `agent/src/praxis/data/ccxt_binance.py`; add a corresponding loader to `backtest/data_loader.py` |
| A new contract | add to `contracts/contracts/`; wire into `contracts/ignition/modules/Praxis.ts`; add Hardhat test |
| A new UI route | add `app/app/<route>/page.tsx`; link from `app/components/nav.tsx:ITEMS` |
| A new hypothesis | row in `docs/HYPOTHESES.md`; mirror notebook in `research/H##_*.ipynb`; pre-register **before** running |

## I want to verify…

| Property | How |
|---|---|
| No look-ahead bias | every feature uses `.shift(1)` before being applied; engine only reads `prices.iloc[: i + 1]` per bar |
| The risk gate is the only chokepoint | grep `git grep -nE 'executor.execute|apply_fill' agent/src/praxis` — only `engine.py` calls them, after `risk_gate.check` |
| No original-author leftovers | `grep -ri "blockch[A]In\|[r]omario\|0x418EBcE\|67c440a8" .` (must be 0 hits — character classes prevent this line itself from matching) |
| Reproducibility | re-run with the same config; the `runs/<ts>_<hash>/` suffix matches; metrics are bit-identical for synthetic data |
| H05 verdict logic was committed pre-run | `research/build_h05.py` shows the verdict function is part of the template, not added after |

---

If you want a topic added to this index, open a PR adding the row.
