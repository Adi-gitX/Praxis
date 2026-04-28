# Reproducing Praxis Results

Every backtest is deterministic given a config + a seed. This document is the
exact recipe.

## Prerequisites

- Python 3.11+
- Node.js 18+
- (Optional) Hardhat-compatible RPC (Base Sepolia) for the contracts side

## 1. Clone and install

```bash
git clone git@github.com:Adi-gitX/Praxis.git
cd Praxis
cd agent && poetry install && cd ..
cd app && npm install && cd ..
cd contracts && npm install && cd ..
```

## 2. Run the headline backtest

```bash
cd agent
poetry run python -m praxis.cli backtest --config configs/trend_following.yaml --runs-dir ../runs
```

This will:

1. Pull BTC / ETH / SOL daily prices from CoinGecko (cached to `.praxis_cache/`).
2. Run `trend_following` from 2024-01-01 to 2024-12-31 with seed=42.
3. Write `runs/<timestamp>_<hash>/` containing `config.yaml`, `decisions.jsonl`,
   `equity_curve.csv`, `trades.csv`, `metrics.json`, and `report.html`.

The hash suffix is a SHA-256 of the canonicalised config; re-running with the
same `configs/trend_following.yaml` will produce the same suffix.

## 3. Open the report

```bash
open runs/<timestamp>_<hash>/report.html
```

Expected metrics on the seeded synthetic universe (offline test path) are
within ±0.05 Sharpe of the values in `metrics.json` produced by `pytest`'s
`test_engine_runs_end_to_end`. Live-data results vary with CoinGecko's
historical-price stream and should be quoted from the run directory itself,
never hard-coded.

## 4. Run the test suite

```bash
cd agent
poetry run pytest -q
```

The smoke suite covers:

- Signals compute with the right shape and warm-up window.
- Kelly sizing signs and caps.
- Drawdown monitor halts at threshold.
- Engine produces a finite equity curve, honours the seed, and trades.
- Walk-forward analysis emits at least two folds with valid Sharpe values.
- Statistics: PSR / DSR monotonicity, bootstrap CI brackets the point.
- Purged k-fold: no overlap between train and test indices.
- HMM regime detection on a two-regime synthetic series.

## 5. Run the UI

```bash
cd app
npm run dev
# http://localhost:3000
```

The UI uses deterministic seeded demo data so every page render shows
identical numbers. To wire it to a live `praxis paper-trade` session, point
`NEXT_PUBLIC_API_URL` at the FastAPI server (planned).

## 6. Determinism contract

| Surface | Determinism source |
|---|---|
| Engine | NumPy seed + ordered iteration over a fixed price index |
| Stats | `numpy.random.default_rng(seed)` for bootstrap |
| Engine paper-trade | Slippage is a deterministic function of size/liquidity (no rand) |
| Run hash | SHA-256 of canonical-JSON of the config dict |
| UI demo data | mulberry32 PRNG with hard-coded seeds per page |

Where determinism is *not* contractual: live data fetches (CoinGecko returns
slightly different timestamps depending on cache state); the LLM meta-policy
when `--llm` is passed (LLM outputs are non-deterministic by design).

## Troubleshooting

- **CoinGecko 429.** Hit the cache: `ls agent/.praxis_cache/prices/`. Delete
  individual cached files to force a re-fetch.
- **`praxis` import error.** From the `agent/` directory, run
  `poetry run python -m praxis.cli ...` rather than invoking `python` directly.
- **Hardhat "module not found".** Run `npm install` from the `contracts/` root.
