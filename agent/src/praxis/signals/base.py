from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class SignalSpec:
    name: str
    lookback: int
    description: str = ""


class Signal(ABC):
    spec: SignalSpec

    @abstractmethod
    def compute(self, prices: pd.DataFrame) -> pd.DataFrame:
        """Return a DataFrame of signal values aligned to `prices.index`.

        Input `prices` is wide-format: index is timestamp, columns are assets.
        Output has the same shape; NaNs are expected for the warm-up window.
        """

    def warmup(self) -> int:
        return self.spec.lookback
