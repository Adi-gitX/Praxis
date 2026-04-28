# praxis-agent

Python core for the Praxis quant trading agent.

```
src/praxis/
├── signals/      numerical signal generators (momentum, mean-reversion, vol, correlation, on-chain)
├── strategies/   signal-to-orders strategies (trend-following, stat-arb, vol-target)
├── policy/       regime detection + LLM meta-policy (LangGraph)
├── risk/         pre-trade risk gate (Kelly sizing, drawdown, exposure caps)
├── execution/    Coinbase CDP wrapper + slippage estimation
├── backtest/     event-driven backtester + walk-forward + metrics + HTML reports
└── state/        run logging and audit trail
```

## Quickstart

```bash
poetry install
poetry run praxis backtest --strategy trend_following --from 2024-01-01 --to 2024-12-31
poetry run praxis paper-trade --strategy trend_following
```
