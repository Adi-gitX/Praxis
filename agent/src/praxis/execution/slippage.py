from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LinearImpact:
    """Linear impact model: slippage_bps = base + k * (notional / liquidity).

    `liquidity` is daily traded volume in USD. The default coefficient `k=10`
    is a reasonable starting point for crypto majors at 1% of ADV; tune per
    venue for live trading. Replace with a square-root-impact model for size
    that's a meaningful fraction of book depth.
    """

    base_bps: float = 5.0
    k: float = 10.0

    def estimate(self, notional: float, liquidity: float) -> float:
        if liquidity <= 0:
            return 1_000.0  # untradeable
        impact = self.k * (abs(notional) / liquidity) * 10_000.0
        return self.base_bps + impact


def estimate_slippage_bps(notional: float, liquidity: float, base_bps: float = 5.0) -> float:
    return LinearImpact(base_bps=base_bps).estimate(notional, liquidity)
