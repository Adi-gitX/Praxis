"""Signals — numerical features computed from price/onchain history.

A Signal is a stateless function: given a price history (and optional auxiliary
data), produce a series of values aligned to the input index. Strategies
combine signals into target weights; the signal layer itself never trades.
"""
from praxis.signals.base import Signal
from praxis.signals.correlation import RollingCorrelation
from praxis.signals.mean_reversion import ZScore
from praxis.signals.momentum import Momentum
from praxis.signals.onchain import OnChainPlaceholder
from praxis.signals.volatility import RealizedVol, VolOfVol

__all__ = [
    "Signal",
    "Momentum",
    "ZScore",
    "RealizedVol",
    "VolOfVol",
    "RollingCorrelation",
    "OnChainPlaceholder",
]
