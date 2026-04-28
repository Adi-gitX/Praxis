from __future__ import annotations

import numpy as np
import pandas as pd

from praxis.signals.base import Signal
from praxis.signals.momentum import Momentum
from praxis.signals.volatility import RealizedVol
from praxis.strategies.base import Strategy, StrategyOutput


class TrendFollowing(Strategy):
    """Time-series trend following with inverse-vol scaling.

    For each asset:
        raw_signal = sign(momentum_lookback) * abs(momentum) ** 0.5
        weight    = clip(raw_signal / realized_vol, -cap, cap)

    Cross-sectionally normalised so absolute weights sum to `gross_target`.
    Long when uptrending, short when downtrending. Sizing is inverse-vol so a
    50%-vol asset gets half the allocation of a 25%-vol asset.
    """

    name = "trend_following"

    def __init__(
        self,
        lookback: int = 60,
        vol_lookback: int = 30,
        per_asset_cap: float = 0.5,
        gross_target: float = 1.0,
    ) -> None:
        self.lookback = lookback
        self.vol_lookback = vol_lookback
        self.per_asset_cap = per_asset_cap
        self.gross_target = gross_target
        self._momentum = Momentum(lookback=lookback)
        self._vol = RealizedVol(lookback=vol_lookback)

    def required_signals(self) -> list[Signal]:
        return [self._momentum, self._vol]

    def step(
        self,
        ts: pd.Timestamp,
        prices: pd.DataFrame,
        signals: dict[str, pd.DataFrame],
    ) -> StrategyOutput:
        mom = signals[self._momentum.spec.name].loc[ts]
        vol = signals[self._vol.spec.name].loc[ts]

        raw = pd.Series(np.sign(mom.to_numpy()) * np.sqrt(np.abs(mom.to_numpy())), index=mom.index)
        scaled = raw / vol.replace(0.0, np.nan)
        weights = scaled.clip(lower=-self.per_asset_cap, upper=self.per_asset_cap)

        # Drop NaNs (warm-up window).
        weights = weights.dropna()
        if weights.empty:
            return StrategyOutput(target_weights={})

        gross = float(weights.abs().sum())
        if gross > 0:
            weights = weights * (self.gross_target / gross)

        attribution = {str(asset): float(w * mom.get(asset, 0.0)) for asset, w in weights.items()}
        return StrategyOutput(
            target_weights={str(asset): float(w) for asset, w in weights.items()},
            signal_snapshot={
                f"momentum[{a}]": float(mom.get(a, float("nan"))) for a in weights.index
            }
            | {f"vol[{a}]": float(vol.get(a, float("nan"))) for a in weights.index},
            attribution=attribution,
            notes=f"gross={float(weights.abs().sum()):.4f}",
        )
