"""Strategies — combine signals into target portfolio weights.

A Strategy never reads market data directly. It receives pre-computed signals
from the signal layer and emits a target-weights mapping {asset: weight in [-1, 1]}.
The engine + risk gate handle conversion to orders.
"""
from typing import Any

from praxis.strategies.base import Strategy, StrategyOutput
from praxis.strategies.stat_arb import StatArb
from praxis.strategies.trend_following import TrendFollowing
from praxis.strategies.vol_target import VolTarget

__all__ = ["Strategy", "StrategyOutput", "TrendFollowing", "StatArb", "VolTarget", "REGISTRY", "build"]


REGISTRY: dict[str, type[Strategy]] = {
    "trend_following": TrendFollowing,
    "stat_arb": StatArb,
    "vol_target": VolTarget,
}


def build(name: str, **params: Any) -> Strategy:
    if name not in REGISTRY:
        raise KeyError(f"Unknown strategy '{name}'. Available: {list(REGISTRY)}")
    return REGISTRY[name](**params)
