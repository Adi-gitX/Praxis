from __future__ import annotations

from dataclasses import dataclass

from praxis.types import Order, PortfolioState, RiskCheck, Side


@dataclass
class ExposureLimits:
    """Per-asset and aggregate exposure caps, expressed as fractions of NAV.

    `per_asset` caps |notional_a| / NAV.
    `gross`     caps sum_a |notional_a| / NAV (leverage proxy).
    `net`       caps sum_a notional_a / NAV (directional bias).

    All three are checked independently and the most restrictive wins. If an
    order would breach a cap, the order is partially filled up to the cap.
    """

    per_asset: float = 0.30
    gross: float = 2.0
    net: float = 1.5

    def check(
        self,
        order: Order,
        portfolio: PortfolioState,
        marks: dict[str, float],
    ) -> RiskCheck:
        nav = max(portfolio.equity(marks), 1e-9)
        signed_qty = order.quantity if order.side == Side.BUY else -order.quantity
        delta_notional = signed_qty * marks.get(order.asset, order.notional / max(order.quantity, 1e-9))

        existing = portfolio.positions.get(order.asset)
        existing_notional = existing.quantity * marks.get(order.asset, existing.avg_price) if existing else 0.0
        new_asset_notional = existing_notional + delta_notional

        per_cap_notional = self.per_asset * nav
        if abs(new_asset_notional) > per_cap_notional:
            allowed_delta = (per_cap_notional - abs(existing_notional)) * (
                1 if signed_qty > 0 else -1
            )
            mark = marks.get(order.asset, 0.0)
            if mark <= 0:
                return RiskCheck(False, "per_asset_cap: missing mark", 0.0)
            allowed_qty = abs(allowed_delta / mark)
            return RiskCheck(
                approved=allowed_qty > 0,
                reason=f"per_asset_cap: trimmed to {allowed_qty:.6f}",
                adjusted_quantity=allowed_qty,
            )

        gross_after = portfolio.gross_exposure - abs(existing_notional) + abs(new_asset_notional)
        if gross_after > self.gross * nav:
            return RiskCheck(False, f"gross_cap: {gross_after / nav:.4f} > {self.gross}", 0.0)

        net_after = portfolio.net_exposure - existing_notional + new_asset_notional
        if abs(net_after) > self.net * nav:
            return RiskCheck(False, f"net_cap: {net_after / nav:.4f} > {self.net}", 0.0)

        return RiskCheck(True, "ok", order.quantity)
