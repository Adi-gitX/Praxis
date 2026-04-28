from __future__ import annotations

import math

import pandas as pd

from praxis._typed_np import log_df
from praxis.signals.base import Signal, SignalSpec


class RealizedVol(Signal):
    """Rolling realized volatility, annualized for crypto (365 trading days)."""

    def __init__(self, lookback: int = 30, annualization: int = 365) -> None:
        if lookback < 2:
            raise ValueError("RealizedVol lookback must be >= 2")
        self.spec = SignalSpec(
            name=f"realized_vol_{lookback}",
            lookback=lookback,
            description=f"Annualized realized vol over {lookback} bars.",
        )
        self.lookback = lookback
        self.annualization = annualization

    def compute(self, prices: pd.DataFrame) -> pd.DataFrame:
        log_returns = log_df(prices).diff()
        rolling_std = log_returns.rolling(self.lookback, min_periods=self.lookback).std(ddof=0)
        return rolling_std * math.sqrt(self.annualization)


class VolOfVol(Signal):
    """Volatility of the realized-vol series — proxy for regime instability."""

    def __init__(self, lookback: int = 30, vol_window: int = 30) -> None:
        self.spec = SignalSpec(
            name=f"vol_of_vol_{vol_window}_{lookback}",
            lookback=lookback + vol_window,
            description="Std of rolling realized vol.",
        )
        self.lookback = lookback
        self.inner = RealizedVol(lookback=vol_window)

    def compute(self, prices: pd.DataFrame) -> pd.DataFrame:
        rv = self.inner.compute(prices)
        return rv.rolling(self.lookback, min_periods=self.lookback).std(ddof=0)
