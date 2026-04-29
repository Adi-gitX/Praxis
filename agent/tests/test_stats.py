"""Sanity tests for the advanced statistics module.

We don't try to test the math against analytic ground truth (PSR/DSR have
no closed form for arbitrary inputs); instead we test invariants:

    * Sharpe of zero-return series is zero.
    * PSR is monotonic in mean-return for fixed vol.
    * DSR <= PSR when n_trials > 1.
    * Bootstrap CI brackets the point estimate.
    * PBO is in [0, 1].
"""
from __future__ import annotations

import numpy as np

from praxis.backtest.purged_kfold import CombinatorialPurgedKFold, PurgedKFold
from praxis.backtest.stats import (
    block_bootstrap_ci,
    deflated_sharpe,
    probabilistic_sharpe,
    probability_of_backtest_overfit,
    sharpe,
)


def _seeded_returns(n: int = 500, mean: float = 0.001, std: float = 0.02, seed: int = 1) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.normal(mean, std, size=n)


def test_sharpe_zero_for_constant_returns() -> None:
    arr = np.full(200, 0.001)
    assert sharpe(arr) == 0.0


def test_psr_monotonic_in_mean() -> None:
    psr_low = probabilistic_sharpe(_seeded_returns(mean=0.0005))
    psr_high = probabilistic_sharpe(_seeded_returns(mean=0.0015))
    assert 0.0 <= psr_low <= 1.0
    assert 0.0 <= psr_high <= 1.0
    assert psr_high > psr_low


def test_deflated_sharpe_at_most_psr() -> None:
    arr = _seeded_returns()
    psr = probabilistic_sharpe(arr)
    dsr = deflated_sharpe(arr, n_trials=20)
    assert dsr <= psr + 1e-9
    assert 0.0 <= dsr <= 1.0


def test_bootstrap_ci_brackets_point_estimate() -> None:
    arr = _seeded_returns(n=400, seed=7)
    point, lo, hi = block_bootstrap_ci(arr, sharpe, n_iter=500, block_size=10, seed=11)
    assert lo <= point <= hi
    assert hi - lo > 0


def test_pbo_range() -> None:
    rng = np.random.default_rng(0)
    matrix = rng.normal(size=(20, 6))  # 20 splits, 6 trials
    pbo = probability_of_backtest_overfit(matrix)
    assert 0.0 <= pbo <= 1.0


def test_purged_kfold_no_overlap() -> None:
    splitter = PurgedKFold(n_splits=4, label_horizon=5, embargo_pct=0.01)
    n = 500
    X = np.arange(n).reshape(-1, 1)
    for train, test in splitter.split(X):
        assert not (set(train) & set(test))
        # Embargo + purge: at least the immediate boundary is purged.
        if len(train) and len(test):
            assert test.min() not in train
            assert test.max() not in train


def test_cpcv_path_count() -> None:
    cpcv = CombinatorialPurgedKFold(n_groups=6, n_test_groups=2)
    assert cpcv.n_paths() == 15  # C(6, 2)
    n = 600
    X = np.arange(n).reshape(-1, 1)
    splits = list(cpcv.split(X))
    assert len(splits) == 15
    for train, test in splits:
        assert not (set(train) & set(test))
