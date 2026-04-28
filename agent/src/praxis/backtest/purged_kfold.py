"""Purged K-Fold cross-validation for time-series.

References:
    López de Prado, M. (2018). Advances in Financial Machine Learning, ch. 7.
        Wiley.

Standard k-fold leaks information in financial time series because labels are
formed from forward-looking windows that overlap test fold boundaries. The
purged variant addresses this by:

    * Purging — dropping training samples whose label-horizon intersects any
      test sample.
    * Embargo — adding a buffer of `embargo_pct` of total samples after each
      test fold during which we also drop training samples.

The API mirrors scikit-learn's `KFold` so it can be dropped into existing
hyperparameter-search code.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Iterator

import numpy as np
import pandas as pd


@dataclass
class PurgedKFold:
    """Purged k-fold split with embargo.

    Parameters
    ----------
    n_splits:
        Number of folds. Test folds are sequential, non-overlapping.
    label_horizon:
        Number of bars over which a sample's label is computed (e.g. for a
        5-bar forward return, set to 5). Training samples whose horizon
        crosses a test fold boundary are purged.
    embargo_pct:
        Fraction of total samples to embargo *after* each test fold. Typical
        values 0.005-0.02 for daily crypto returns.
    """

    n_splits: int = 5
    label_horizon: int = 1
    embargo_pct: float = 0.01

    def split(self, X: pd.DataFrame | np.ndarray) -> Iterator[tuple[np.ndarray, np.ndarray]]:
        if self.n_splits < 2:
            raise ValueError("n_splits must be >= 2")
        n = len(X)
        embargo = int(round(self.embargo_pct * n))
        fold_size = n // self.n_splits
        indices = np.arange(n)
        for k in range(self.n_splits):
            test_start = k * fold_size
            test_end = (k + 1) * fold_size if k < self.n_splits - 1 else n
            test = indices[test_start:test_end]
            keep = np.ones(n, dtype=bool)
            keep[test_start : test_end + embargo] = False
            # Purge training samples whose forward-label horizon crosses test:
            purge_lo = max(0, test_start - self.label_horizon)
            keep[purge_lo:test_start] = False
            train = indices[keep]
            yield train, test

    def get_n_splits(self) -> int:
        return self.n_splits


@dataclass
class CombinatorialPurgedKFold:
    """Combinatorial Purged K-Fold (CPCV) — López de Prado (2018), ch. 12.

    Each split holds out `n_test_groups` of `n_groups` total groups; the rest
    is the training set. Iterating over all C(n_groups, n_test_groups) such
    selections produces multiple non-overlapping backtest paths from a single
    dataset, dramatically improving the statistical resolution of out-of-sample
    Sharpe estimates compared to a single split.

    The output of `split` is the sequence of (train_idx, test_idx) tuples;
    `path_indices` returns, for each backtest path, the test-fold mapping.
    """

    n_groups: int = 6
    n_test_groups: int = 2
    label_horizon: int = 1
    embargo_pct: float = 0.01

    def __post_init__(self) -> None:
        if self.n_test_groups < 1 or self.n_test_groups >= self.n_groups:
            raise ValueError("Need 1 <= n_test_groups < n_groups")

    def _group_bounds(self, n: int) -> list[tuple[int, int]]:
        size = n // self.n_groups
        bounds = []
        for k in range(self.n_groups):
            lo = k * size
            hi = (k + 1) * size if k < self.n_groups - 1 else n
            bounds.append((lo, hi))
        return bounds

    def split(self, X: pd.DataFrame | np.ndarray) -> Iterator[tuple[np.ndarray, np.ndarray]]:
        n = len(X)
        bounds = self._group_bounds(n)
        embargo = int(round(self.embargo_pct * n))
        indices = np.arange(n)
        for combo in combinations(range(self.n_groups), self.n_test_groups):
            test_mask = np.zeros(n, dtype=bool)
            for g in combo:
                lo, hi = bounds[g]
                test_mask[lo:hi] = True
            test = indices[test_mask]
            keep = ~test_mask
            for g in combo:
                lo, hi = bounds[g]
                purge_lo = max(0, lo - self.label_horizon)
                keep[purge_lo:lo] = False
                keep[hi : hi + embargo] = False
            train = indices[keep]
            yield train, test

    def n_paths(self) -> int:
        from math import comb
        return comb(self.n_groups, self.n_test_groups)
