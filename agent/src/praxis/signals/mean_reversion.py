from __future__ import annotations

import pandas as pd

from praxis.signals.base import Signal, SignalSpec


class ZScore(Signal):
    """Rolling z-score of price against its trailing mean.

    Large positive z => price is rich vs. its window; mean-reversion strategies
    short. Large negative z => cheap; strategies go long.
    """

    def __init__(self, lookback: int = 60) -> None:
        if lookback < 5:
            raise ValueError("ZScore lookback must be >= 5")
        self.spec = SignalSpec(
            name=f"zscore_{lookback}",
            lookback=lookback,
            description=f"Z-score of price over {lookback} bars.",
        )
        self.lookback = lookback

    def compute(self, prices: pd.DataFrame) -> pd.DataFrame:
        rolling = prices.rolling(self.lookback, min_periods=self.lookback)
        mean = rolling.mean()
        std = rolling.std(ddof=0)
        return (prices - mean) / std.replace(0.0, pd.NA)
