from __future__ import annotations

import pandas as pd

from praxis._typed_np import log_df
from praxis.signals.base import Signal, SignalSpec


class RollingCorrelation(Signal):
    """Rolling pairwise correlation matrix.

    Output is wide-format with multiindex columns (asset_a, asset_b). Stat-arb
    strategies pull a single pair; the risk layer reads the average pairwise
    correlation as a portfolio-level concentration proxy.
    """

    def __init__(self, lookback: int = 60) -> None:
        if lookback < 10:
            raise ValueError("Correlation lookback must be >= 10")
        self.spec = SignalSpec(
            name=f"correlation_{lookback}",
            lookback=lookback,
            description=f"Pairwise correlation over {lookback} bars.",
        )
        self.lookback = lookback

    def compute(self, prices: pd.DataFrame) -> pd.DataFrame:
        returns = log_df(prices).diff()
        assets = [str(c) for c in returns.columns]
        pairs = [(a, b) for i, a in enumerate(assets) for b in assets[i + 1 :]]

        out = pd.DataFrame(index=returns.index, columns=pd.MultiIndex.from_tuples(pairs))
        for a, b in pairs:
            out[(a, b)] = returns[a].rolling(self.lookback, min_periods=self.lookback).corr(
                returns[b]
            )
        return out
