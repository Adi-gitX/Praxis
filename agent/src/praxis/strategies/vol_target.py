from __future__ import annotations

import numpy as np
import pandas as pd

from praxis.signals.base import Signal
from praxis.signals.volatility import RealizedVol
from praxis.strategies.base import Strategy, StrategyOutput


class VolTarget(Strategy):
    """Volatility-targeted long-only exposure.

    Each asset is weighted inversely to its realized vol so the resulting
    portfolio targets `target_vol` (annualized). Equal-risk-contribution at
    the 1-asset level; weights are then renormalised to sum to `gross`.
    """

    name = "vol_target"

    def __init__(
        self,
        target_vol: float = 0.20,
        vol_lookback: int = 30,
        gross: float = 1.0,
        per_asset_cap: float = 0.5,
    ) -> None:
        self.target_vol = target_vol
        self.vol_lookback = vol_lookback
        self.gross = gross
        self.per_asset_cap = per_asset_cap
        self._vol = RealizedVol(lookback=vol_lookback)

    def required_signals(self) -> list[Signal]:
        return [self._vol]

    def step(
        self,
        ts: pd.Timestamp,
        prices: pd.DataFrame,
        signals: dict[str, pd.DataFrame],
    ) -> StrategyOutput:
        vol = signals[self._vol.spec.name].loc[ts]
        inv_vol = (1.0 / vol.replace(0.0, np.nan)).dropna()
        if inv_vol.empty:
            return StrategyOutput(target_weights={})

        raw = self.target_vol * inv_vol
        capped = raw.clip(upper=self.per_asset_cap)
        gross_now = capped.sum()
        if gross_now > 0:
            weights = capped * (self.gross / gross_now)
        else:
            weights = capped

        return StrategyOutput(
            target_weights={str(a): float(w) for a, w in weights.items()},
            signal_snapshot={f"vol[{a}]": float(vol.get(a, float("nan"))) for a in weights.index},
            attribution={str(a): float(self.target_vol / vol.get(a, float("nan"))) for a in weights.index},
            notes=f"gross={float(weights.sum()):.4f} target_vol={self.target_vol:.2f}",
        )
