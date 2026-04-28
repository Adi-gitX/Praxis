from __future__ import annotations

import pandas as pd

from praxis.signals.base import Signal, SignalSpec


class OnChainPlaceholder(Signal):
    """Interface stub for on-chain signals (TVL change, large-wallet moves, funding,
    gas patterns).

    Real implementations plug into The Graph / on-chain RPC. Until that wiring
    lands, this returns NaN of the right shape so the rest of the pipeline can
    be exercised end-to-end without pretending we have data we don't.
    """

    def __init__(self, lookback: int = 7, signal_name: str = "onchain_tvl_change") -> None:
        self.spec = SignalSpec(
            name=signal_name,
            lookback=lookback,
            description="On-chain feature placeholder; returns NaN.",
        )
        self.lookback = lookback

    def compute(self, prices: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame(index=prices.index, columns=prices.columns, dtype=float)
