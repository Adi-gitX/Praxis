"""End-to-end smoke test on synthetic prices — does the full pipeline run?

This test never hits the network. It generates a deterministic price grid,
runs trend-following through the engine + risk gate + paper executor, and
asserts the equity curve has the right shape and no NaNs leaked through.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from praxis.backtest.engine import BacktestEngine
from praxis.backtest.metrics import compute_metrics, walk_forward
from praxis.policy.meta_policy import RuleBasedPolicy
from praxis.risk.drawdown import DrawdownMonitor
from praxis.risk.exposure import ExposureLimits
from praxis.risk.gate import RiskGate
from praxis.risk.kelly import fractional_kelly
from praxis.signals.momentum import Momentum
from praxis.signals.mean_reversion import ZScore
from praxis.signals.volatility import RealizedVol
from praxis.strategies.trend_following import TrendFollowing


def _synthetic_prices(seed: int = 42, n: int = 365, assets: tuple[str, ...] = ("BTC", "ETH", "SOL")) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    drifts = {"BTC": 0.0008, "ETH": 0.0006, "SOL": 0.0004}
    vols = {"BTC": 0.03, "ETH": 0.04, "SOL": 0.06}
    out = {}
    for a in assets:
        rets = rng.normal(drifts[a], vols[a], size=n)
        out[a] = 100.0 * np.exp(np.cumsum(rets))
    return pd.DataFrame(out, index=dates)


def test_signals_compute_aligned() -> None:
    prices = _synthetic_prices()
    mom = Momentum(lookback=30).compute(prices)
    zsc = ZScore(lookback=60).compute(prices)
    vol = RealizedVol(lookback=30).compute(prices)

    assert mom.shape == prices.shape
    assert zsc.shape == prices.shape
    assert vol.shape == prices.shape
    assert mom.iloc[:30].isna().all().all()
    assert mom.iloc[40:].notna().all().all()
    assert (vol.dropna() >= 0).all().all()


def test_kelly_signs_and_caps() -> None:
    assert fractional_kelly(0.10, 0.04, 0.5) == pytest.approx(1.0)  # capped
    assert fractional_kelly(-0.10, 0.04, 0.5) == pytest.approx(-1.0)  # capped
    assert fractional_kelly(0.0, 0.04) == 0.0
    assert fractional_kelly(0.05, 0.0) == 0.0  # zero variance => zero size
    assert 0 < fractional_kelly(0.02, 0.04, fraction=0.25) < 0.25


def test_drawdown_halts() -> None:
    dd = DrawdownMonitor(max_drawdown=0.10)
    dd.update(100.0)
    assert not dd.halted
    dd.update(95.0)
    assert not dd.halted
    dd.update(89.9)
    assert dd.halted


def test_engine_runs_end_to_end() -> None:
    prices = _synthetic_prices()
    engine = BacktestEngine(
        prices=prices,
        strategies=[TrendFollowing(lookback=30, vol_lookback=20, gross_target=1.0)],
        risk_gate=RiskGate(
            drawdown=DrawdownMonitor(max_drawdown=0.50),
            exposure=ExposureLimits(per_asset=0.6, gross=2.0, net=1.5),
        ),
        meta_policy=RuleBasedPolicy(),
        initial_cash=1_000_000.0,
    )
    result = engine.run()

    assert len(result.equity_curve) == len(prices)
    assert result.equity_curve.notna().all()
    assert result.equity_curve.iloc[0] == pytest.approx(1_000_000.0, rel=1e-9)
    assert len(result.trades) > 0  # something traded

    metrics = compute_metrics(result.equity_curve)
    assert metrics.n_periods == len(prices) - 1
    assert np.isfinite(metrics.sharpe)
    assert metrics.max_drawdown >= 0


def test_walk_forward_produces_folds() -> None:
    prices = _synthetic_prices(n=400)

    def runner(slice_: pd.DataFrame) -> pd.Series:
        engine = BacktestEngine(
            prices=slice_,
            strategies=[TrendFollowing(lookback=20, vol_lookback=10)],
            initial_cash=1_000_000.0,
        )
        return engine.run().equity_curve

    folds = walk_forward(prices, runner, train_window=120, test_window=60)
    assert len(folds) >= 2
    for col in ("sharpe", "max_drawdown", "total_return"):
        assert col in folds.columns
