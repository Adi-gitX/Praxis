from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from praxis.signals.base import Signal


@dataclass
class StrategyOutput:
    target_weights: dict[str, float]
    signal_snapshot: dict[str, float] = field(default_factory=dict)
    attribution: dict[str, float] = field(default_factory=dict)
    notes: str = ""


class Strategy(ABC):
    name: str

    @abstractmethod
    def required_signals(self) -> list[Signal]:
        ...

    @abstractmethod
    def step(
        self,
        ts: pd.Timestamp,
        prices: pd.DataFrame,
        signals: dict[str, pd.DataFrame],
    ) -> StrategyOutput:
        """Produce target weights for `ts` given the latest prices and signals.

        `signals` is keyed by `Signal.spec.name`. Implementations should index
        into the relevant frame at `ts` and never look beyond it.
        """

    def warmup(self) -> int:
        return max((s.warmup() for s in self.required_signals()), default=0)

    def params(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
