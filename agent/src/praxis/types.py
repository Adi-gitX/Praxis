"""Core dataclasses passed between layers.

Every value crossing a layer boundary (signal -> strategy -> risk -> execution)
is one of these. Keeping them dataclasses (not arbitrary dicts) means a typo
fails at construction, not three layers later.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class Side(str, Enum):
    BUY = "buy"
    SELL = "sell"


class Regime(str, Enum):
    TRENDING = "trending"
    RANGING = "ranging"
    HIGH_VOL = "high_vol"
    CRISIS = "crisis"


@dataclass(frozen=True)
class Bar:
    ts: datetime
    asset: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class SignalValue:
    name: str
    asset: str
    ts: datetime
    value: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Order:
    asset: str
    side: Side
    quantity: float
    notional: float
    ts: datetime
    strategy: str
    rationale: dict[str, Any] = field(default_factory=dict)


@dataclass
class Position:
    asset: str
    quantity: float
    avg_price: float

    @property
    def notional(self) -> float:
        return self.quantity * self.avg_price


@dataclass
class PortfolioState:
    cash: float
    positions: dict[str, Position] = field(default_factory=dict)
    equity_curve: list[tuple[datetime, float]] = field(default_factory=list)

    @property
    def gross_exposure(self) -> float:
        return sum(abs(p.notional) for p in self.positions.values())

    @property
    def net_exposure(self) -> float:
        return sum(p.notional for p in self.positions.values())

    def equity(self, marks: dict[str, float]) -> float:
        return self.cash + sum(
            pos.quantity * marks.get(pos.asset, pos.avg_price)
            for pos in self.positions.values()
        )


@dataclass(frozen=True)
class RiskCheck:
    approved: bool
    reason: str
    adjusted_quantity: float | None = None


@dataclass(frozen=True)
class Decision:
    ts: datetime
    regime: Regime
    signals: dict[str, float]
    target_weights: dict[str, float]
    orders: list[Order]
    risk_checks: list[RiskCheck]
    notes: str = ""
