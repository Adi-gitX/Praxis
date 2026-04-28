from __future__ import annotations

import numpy as np
import pandas as pd

from praxis.signals.base import Signal
from praxis.signals.mean_reversion import ZScore
from praxis.strategies.base import Strategy, StrategyOutput


class StatArb(Strategy):
    """Pair-trade between two assets using z-score of the log spread.

    Spread definition:
        spread_t = log(asset_a_t) - beta * log(asset_b_t)

    where `beta` is fitted online via rolling OLS over `lookback` bars. The
    z-score of `spread` drives entry/exit:

        z >  entry  =>  short A, long B (spread is rich)
        z < -entry  =>  long  A, short B (spread is cheap)
        |z| < exit  =>  flat

    Position size is `target_weight` per leg. This is a single-pair
    implementation; portfolios of pairs compose at the policy layer.
    """

    name = "stat_arb"

    def __init__(
        self,
        asset_a: str,
        asset_b: str,
        lookback: int = 60,
        z_entry: float = 2.0,
        z_exit: float = 0.5,
        target_weight: float = 0.5,
    ) -> None:
        if asset_a == asset_b:
            raise ValueError("StatArb requires two distinct assets")
        self.asset_a = asset_a
        self.asset_b = asset_b
        self.lookback = lookback
        self.z_entry = z_entry
        self.z_exit = z_exit
        self.target_weight = target_weight
        self._z = ZScore(lookback=lookback)
        self._last_state: int = 0

    def required_signals(self) -> list[Signal]:
        return [self._z]

    def _spread(self, prices: pd.DataFrame, end_ts: pd.Timestamp) -> tuple[pd.Series, float]:
        window = prices.loc[:end_ts].tail(self.lookback)
        if len(window) < self.lookback:
            return pd.Series(dtype=float), float("nan")
        log_a_arr = np.log(window[self.asset_a].to_numpy(dtype=float))
        log_b_arr = np.log(window[self.asset_b].to_numpy(dtype=float))
        b_var = float(log_b_arr.var(ddof=0))
        beta = float(np.cov(log_a_arr, log_b_arr, ddof=0)[0, 1] / b_var) if b_var > 0 else 1.0
        spread = pd.Series(log_a_arr - beta * log_b_arr, index=window.index)
        return spread, beta

    def step(
        self,
        ts: pd.Timestamp,
        prices: pd.DataFrame,
        signals: dict[str, pd.DataFrame],
    ) -> StrategyOutput:
        spread, beta = self._spread(prices, ts)
        if spread.empty or spread.isna().all():
            return StrategyOutput(target_weights={self.asset_a: 0.0, self.asset_b: 0.0})

        mu = float(spread.mean())
        sigma = float(spread.std(ddof=0))
        z = (spread.iloc[-1] - mu) / sigma if sigma > 0 else 0.0

        if z > self.z_entry:
            self._last_state = -1  # short A, long B
        elif z < -self.z_entry:
            self._last_state = 1  # long A, short B
        elif abs(z) < self.z_exit:
            self._last_state = 0

        w_a = self._last_state * self.target_weight
        w_b = -self._last_state * self.target_weight
        return StrategyOutput(
            target_weights={self.asset_a: w_a, self.asset_b: w_b},
            signal_snapshot={"spread_z": float(z), "beta": beta},
            attribution={self.asset_a: float(z * w_a), self.asset_b: float(-z * w_b)},
            notes=f"state={self._last_state} z={z:.4f}",
        )
