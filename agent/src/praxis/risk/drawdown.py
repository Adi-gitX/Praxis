from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DrawdownMonitor:
    """Tracks the equity high-water mark and current drawdown.

    `should_halt(equity)` becomes True once peak-to-trough drawdown crosses
    `max_drawdown`. Once tripped, it stays tripped — manual reset only. The
    backtester and live engine both honour this as a hard kill.
    """

    max_drawdown: float = 0.25
    peak: float = 0.0
    halted: bool = False

    def update(self, equity: float) -> float:
        if equity > self.peak:
            self.peak = equity
        if self.peak <= 0:
            return 0.0
        dd = (self.peak - equity) / self.peak
        if dd >= self.max_drawdown:
            self.halted = True
        return dd

    def should_halt(self, equity: float) -> tuple[bool, float]:
        dd = self.update(equity)
        return self.halted, dd

    def reset(self) -> None:
        self.peak = 0.0
        self.halted = False
