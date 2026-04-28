"""Backtester — event-driven, deterministic, with walk-forward + purged-kfold validation."""
from praxis.backtest.data_loader import CoinGeckoLoader, load_csv
from praxis.backtest.engine import BacktestEngine, BacktestResult
from praxis.backtest.metrics import compute_metrics, walk_forward
from praxis.backtest.purged_kfold import CombinatorialPurgedKFold, PurgedKFold
from praxis.backtest.report import write_html_report
from praxis.backtest.stats import (
    StatsReport,
    block_bootstrap_ci,
    deflated_sharpe,
    full_report,
    probabilistic_sharpe,
    probability_of_backtest_overfit,
)

__all__ = [
    "BacktestEngine",
    "BacktestResult",
    "CoinGeckoLoader",
    "load_csv",
    "compute_metrics",
    "walk_forward",
    "write_html_report",
    "PurgedKFold",
    "CombinatorialPurgedKFold",
    "StatsReport",
    "block_bootstrap_ci",
    "deflated_sharpe",
    "full_report",
    "probabilistic_sharpe",
    "probability_of_backtest_overfit",
]
