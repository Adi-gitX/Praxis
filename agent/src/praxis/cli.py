"""Command-line entry point.

Usage:
    python -m praxis.cli backtest --config configs/trend_following.yaml
    python -m praxis.cli paper-trade --config configs/trend_following.yaml
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, cast

import pandas as pd

from praxis.backtest.data_loader import BinanceDailyLoader, CoinGeckoLoader, load_csv
from praxis.backtest.engine import BacktestEngine
from praxis.backtest.metrics import compute_metrics
from praxis.backtest.report import write_html_report
from praxis.config import BacktestConfig, load
from praxis.policy.meta_policy import LLMMetaPolicy, RuleBasedPolicy
from praxis.policy.regime_detector import RegimeDetector
from praxis.risk.drawdown import DrawdownMonitor
from praxis.risk.exposure import ExposureLimits
from praxis.risk.gate import RiskGate
from praxis.state.run_recorder import RunRecorder
from praxis.strategies import REGISTRY as STRATEGY_REGISTRY
from praxis.strategies import build as build_strategy

log = logging.getLogger("praxis")


def _build_engine(cfg: BacktestConfig, prices: pd.DataFrame, run_dir: Path | None, use_llm: bool) -> BacktestEngine:
    strategy = build_strategy(cfg.strategy, **cfg.strategy_params)
    risk_gate = RiskGate(
        drawdown=DrawdownMonitor(max_drawdown=cfg.risk.max_drawdown),
        exposure=ExposureLimits(
            per_asset=cfg.risk.per_asset_cap,
            gross=cfg.risk.gross_cap,
            net=cfg.risk.net_cap,
        ),
    )
    meta_policy = LLMMetaPolicy() if use_llm else RuleBasedPolicy()
    recorder = None
    if run_dir is not None:
        recorder = RunRecorder(run_dir, config_payload=_summarise(cfg))
    return BacktestEngine(
        prices=prices,
        strategies=[strategy],
        risk_gate=risk_gate,
        meta_policy=meta_policy,
        regime_detector=RegimeDetector(),
        initial_cash=cfg.initial_cash,
        run_recorder=recorder,
    )


def _summarise(cfg: BacktestConfig) -> dict[str, Any]:
    return {
        "name": cfg.name,
        "strategy": cfg.strategy,
        "universe": cfg.universe,
        "start": cfg.start,
        "end": cfg.end,
        "initial_cash": cfg.initial_cash,
        "rebalance": cfg.rebalance,
        "seed": cfg.seed,
        "fee_bps": cfg.fee_bps,
        "slippage_bps": cfg.slippage_bps,
        "strategy_params": cfg.strategy_params,
        "risk": cfg.risk.__dict__,
    }


def _load_prices(cfg: BacktestConfig, prices_csv: str | None, source: str = "binance") -> pd.DataFrame:
    if prices_csv:
        df = load_csv(prices_csv)
        cols = [c for c in df.columns if c in cfg.universe]
        windowed = df[(df.index >= cfg.start) & (df.index <= cfg.end)]
        return windowed[cols]
    if source == "coingecko":
        return CoinGeckoLoader().load(cfg.universe, cfg.start, cfg.end)
    return BinanceDailyLoader().load(cfg.universe, cfg.start, cfg.end)


def cmd_backtest(args: argparse.Namespace) -> int:
    cfg = load(args.config)
    prices = _load_prices(cfg, args.prices_csv, source=args.source)
    runs_root = Path(args.runs_dir)
    engine = _build_engine(cfg, prices, runs_root, use_llm=args.llm)
    log.info("Running backtest %s on %s assets, %d bars", cfg.name, len(prices.columns), len(prices))
    result = engine.run()

    metrics = compute_metrics(result.equity_curve)
    log.info(
        "Sharpe=%.4f Sortino=%.4f MaxDD=%.4f TotalReturn=%.4f",
        metrics.sharpe, metrics.sortino, metrics.max_drawdown, metrics.total_return,
    )

    if engine.run_recorder is not None:
        engine.run_recorder.save_equity(result.equity_curve)
        engine.run_recorder.save_trades(result.trades)
        engine.run_recorder.save_metrics(metrics.as_dict())
        write_html_report(
            engine.run_recorder.dir / "report.html",
            name=cfg.name,
            metrics=metrics,
            equity=result.equity_curve,
            trades=result.trades,
            config_summary={k: str(v) for k, v in _summarise(cfg).items()},
        )
        engine.run_recorder.close()
        log.info("Run dumped to %s", engine.run_recorder.dir)
    return 0


def cmd_paper_trade(args: argparse.Namespace) -> int:
    log.warning("Paper-trade live mode is wired but disabled in this scaffold; "
                "use `backtest` against historical data for now.")
    return 0


def cmd_list_strategies(_: argparse.Namespace) -> int:
    for name in STRATEGY_REGISTRY:
        print(name)
    return 0


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(prog="praxis")
    sub = parser.add_subparsers(dest="cmd", required=True)

    bt = sub.add_parser("backtest", help="Run a backtest from a config file.")
    bt.add_argument("--config", required=True, help="Path to backtest YAML config.")
    bt.add_argument("--prices-csv", default=None, help="Optional path to historical CSV; bypasses online loaders.")
    bt.add_argument("--source", choices=["binance", "coingecko"], default="binance",
                    help="Online price source. Default 'binance' (no API key needed); 'coingecko' requires COINGECKO_API_KEY.")
    bt.add_argument("--runs-dir", default="runs", help="Where to write per-run output.")
    bt.add_argument("--llm", action="store_true", help="Use LLM meta-policy (requires OPENAI_API_KEY).")
    bt.set_defaults(fn=cmd_backtest)

    pt = sub.add_parser("paper-trade", help="Live paper-trading mode (placeholder).")
    pt.add_argument("--config", required=True)
    pt.set_defaults(fn=cmd_paper_trade)

    ls = sub.add_parser("strategies", help="List available strategies.")
    ls.set_defaults(fn=cmd_list_strategies)

    args = parser.parse_args(argv)
    return cast(int, args.fn(args))


if __name__ == "__main__":
    sys.exit(main())
