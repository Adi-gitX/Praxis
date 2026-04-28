from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from praxis._typed_np import log_df
from praxis.types import Regime


@dataclass
class RegimeDetector:
    """Lightweight regime classifier driven by realized vol + trend strength.

    Buckets:
        crisis     — recent vol > 95th percentile of long-window vol distribution
        high_vol   — recent vol > 80th percentile
        trending   — |mean log-return| / vol > trend_threshold
        ranging    — otherwise

    Deliberately simple. Plugging in a HMM or change-point detector is a
    drop-in replacement at the `classify` boundary.
    """

    short_vol_window: int = 14
    long_vol_window: int = 180
    trend_window: int = 30
    trend_threshold: float = 0.5
    high_vol_pct: float = 0.80
    crisis_pct: float = 0.95

    def classify(self, prices: pd.DataFrame) -> Regime:
        if len(prices) < self.long_vol_window:
            return Regime.RANGING

        log_ret = log_df(prices).diff().dropna(how="all")
        # Cross-sectional mean: treat the universe as one risk asset.
        portfolio = log_ret.mean(axis=1)

        rolling_vol = portfolio.rolling(self.short_vol_window, min_periods=self.short_vol_window).std(ddof=0)
        long_vol = portfolio.rolling(self.long_vol_window, min_periods=self.long_vol_window).std(ddof=0)
        if rolling_vol.dropna().empty or long_vol.dropna().empty:
            return Regime.RANGING

        recent_vol = float(rolling_vol.iloc[-1])
        long_vol_dist = rolling_vol.dropna().iloc[-self.long_vol_window:]
        if long_vol_dist.empty:
            return Regime.RANGING

        crisis_threshold = float(long_vol_dist.quantile(self.crisis_pct))
        high_vol_threshold = float(long_vol_dist.quantile(self.high_vol_pct))

        if recent_vol >= crisis_threshold:
            return Regime.CRISIS
        if recent_vol >= high_vol_threshold:
            return Regime.HIGH_VOL

        recent_window = portfolio.tail(self.trend_window)
        if recent_window.empty or recent_window.std(ddof=0) == 0:
            return Regime.RANGING
        trend_strength = abs(recent_window.mean()) / recent_window.std(ddof=0)
        if trend_strength >= self.trend_threshold:
            return Regime.TRENDING
        return Regime.RANGING
