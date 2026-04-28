from __future__ import annotations

from dataclasses import dataclass, field

from praxis.risk.drawdown import DrawdownMonitor
from praxis.risk.exposure import ExposureLimits
from praxis.types import Order, PortfolioState, RiskCheck


@dataclass
class RiskGate:
    """Single chokepoint between policy and execution.

    Every order passes through `check`. Returns a RiskCheck whose
    `approved` flag is False -> drop, True with `adjusted_quantity != original`
    -> partial fill at the trimmed size, True with same -> pass through.

    The drawdown monitor is shared across calls (stateful); exposure limits
    are stateless and recomputed against the live portfolio each call.
    """

    drawdown: DrawdownMonitor = field(default_factory=DrawdownMonitor)
    exposure: ExposureLimits = field(default_factory=ExposureLimits)

    def check(
        self,
        order: Order,
        portfolio: PortfolioState,
        marks: dict[str, float],
    ) -> RiskCheck:
        equity = portfolio.equity(marks)
        halted, dd = self.drawdown.should_halt(equity)
        if halted:
            return RiskCheck(
                approved=False,
                reason=f"drawdown_circuit: dd={dd:.4f} >= {self.drawdown.max_drawdown}",
                adjusted_quantity=0.0,
            )

        return self.exposure.check(order, portfolio, marks)

    def status(self, portfolio: PortfolioState, marks: dict[str, float]) -> dict[str, float]:
        equity = portfolio.equity(marks)
        nav = max(equity, 1e-9)
        return {
            "equity": equity,
            "drawdown": (self.drawdown.peak - equity) / self.drawdown.peak
            if self.drawdown.peak > 0
            else 0.0,
            "drawdown_limit": self.drawdown.max_drawdown,
            "gross_exposure_pct": portfolio.gross_exposure / nav,
            "net_exposure_pct": portfolio.net_exposure / nav,
            "halted": float(self.drawdown.halted),
        }
