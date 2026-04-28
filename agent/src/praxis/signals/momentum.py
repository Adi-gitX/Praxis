from __future__ import annotations

import pandas as pd

from praxis._typed_np import log_df
from praxis.signals.base import Signal, SignalSpec


class Momentum(Signal):
    """Time-series momentum: log-return over a configurable lookback.

    Positive values imply uptrend strength; values are unitless log-returns.
    Used directly by trend-following strategies and as a regime input.
    """

    def __init__(self, lookback: int = 30) -> None:
        if lookback < 2:
            raise ValueError("Momentum lookback must be >= 2")
        self.spec = SignalSpec(
            name=f"momentum_{lookback}",
            lookback=lookback,
            description=f"Log-return over {lookback} bars.",
        )
        self.lookback = lookback

    def compute(self, prices: pd.DataFrame) -> pd.DataFrame:
        log_p = log_df(prices)
        return log_p - log_p.shift(self.lookback)
