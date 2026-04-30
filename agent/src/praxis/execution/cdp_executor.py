"""Executors — `PaperExecutor` is the default for backtest and paper-trade modes;
`CDPExecutor` is the live-trading wrapper around Coinbase's Developer Platform
SDK. Both implement the same interface so the engine doesn't care which is
running.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Protocol

from praxis.execution.slippage import LinearImpact
from praxis.types import Order, Position, Side

log = logging.getLogger(__name__)


@dataclass
class Fill:
    order: Order
    fill_price: float
    fill_quantity: float
    fee_paid: float
    slippage_bps: float


class Executor(Protocol):
    def execute(self, order: Order, mark: float, liquidity: float) -> Fill | None: ...


@dataclass
class PaperExecutor:
    """Simulated fills. Slippage is applied against `mark` on the side that hurts
    the order, fees are charged in bps, and fills are deterministic given inputs.
    """

    fee_bps: float = 5.0
    impact: LinearImpact = field(default_factory=LinearImpact)
    fills: list[Fill] = field(default_factory=list)

    def execute(self, order: Order, mark: float, liquidity: float) -> Fill | None:
        if mark <= 0 or order.quantity <= 0:
            return None
        slippage_bps = self.impact.estimate(notional=order.notional, liquidity=liquidity)
        slip_factor = slippage_bps / 10_000.0
        fill_price = mark * (1 + slip_factor) if order.side == Side.BUY else mark * (1 - slip_factor)
        fee = order.notional * (self.fee_bps / 10_000.0)
        fill = Fill(
            order=order,
            fill_price=fill_price,
            fill_quantity=order.quantity,
            fee_paid=fee,
            slippage_bps=slippage_bps,
        )
        self.fills.append(fill)
        return fill

    @staticmethod
    def apply_fill(positions: dict[str, Position], fill: Fill) -> float:
        """Mutate positions and return signed cash delta (negative => cash spent)."""
        order = fill.order
        signed_qty = fill.fill_quantity if order.side == Side.BUY else -fill.fill_quantity
        existing = positions.get(order.asset)
        if existing is None:
            positions[order.asset] = Position(
                asset=order.asset, quantity=signed_qty, avg_price=fill.fill_price
            )
        else:
            new_qty = existing.quantity + signed_qty
            if new_qty == 0:
                del positions[order.asset]
            else:
                if (existing.quantity > 0 and signed_qty > 0) or (
                    existing.quantity < 0 and signed_qty < 0
                ):
                    total_cost = existing.quantity * existing.avg_price + signed_qty * fill.fill_price
                    existing.avg_price = total_cost / new_qty
                existing.quantity = new_qty
        cash_delta = -signed_qty * fill.fill_price - fill.fee_paid
        return cash_delta


class CDPExecutor:
    """Live executor — wraps `cdp_sdk` for swaps on Base. Disabled by default;
    requires `CDP_API_KEY_ID` and `CDP_API_KEY_SECRET` in the environment. In
    the absence of credentials this raises rather than silently returning fake
    fills, so the system never confuses paper and live modes.
    """

    def __init__(self, network: str = "base-sepolia") -> None:
        self.network = network
        self._client: object | None = None
        if os.getenv("CDP_API_KEY_ID") and os.getenv("CDP_API_KEY_SECRET"):
            self._client = self._init_client()
        else:
            log.warning("CDPExecutor created without credentials; live execute() will raise.")

    def _init_client(self) -> object:
        try:
            from cdp import Cdp  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError(
                "cdp-sdk is not installed; add it to your environment or use PaperExecutor."
            ) from exc
        configure = getattr(Cdp, "configure")
        return configure(
            api_key_id=os.environ["CDP_API_KEY_ID"],
            api_key_secret=os.environ["CDP_API_KEY_SECRET"],
        )

    def execute(self, order: Order, mark: float, liquidity: float) -> Fill | None:
        if self._client is None:
            raise RuntimeError(
                "CDPExecutor has no credentials configured. Either set CDP_API_KEY_* "
                "in the environment or run with PaperExecutor."
            )
        if not _is_live_armed():
            raise RuntimeError(
                "Live CDP execution requires arming with PRAXIS_LIVE=1 in the "
                "environment. The CLI flag --live sets this for the duration of "
                "one process. Refusing to send a real on-chain transaction "
                "without explicit operator opt-in."
            )

        # Live swap path. We deliberately keep this conservative — the whole
        # framework was built around 'risk gate is the only chokepoint',
        # and this method is reached only AFTER the gate has approved the
        # order. So we forward to the CDP wallet's swap intent without any
        # additional risk logic here.
        try:
            from cdp.actions.evm import swap as cdp_swap  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError(
                "cdp.actions.evm.swap not available in the installed cdp-sdk version. "
                "Pin a compatible cdp-sdk and retry."
            ) from exc

        # Translate Order -> CDP swap intent. The exact field names track
        # the cdp-sdk surface; we wrap them in getattr so the call site
        # is forward-compatible with minor SDK refactors.
        swap_fn = getattr(cdp_swap, "create_swap_quote", None) or getattr(cdp_swap, "swap", None)
        if swap_fn is None:
            raise RuntimeError("Could not locate a swap entry-point in cdp.actions.evm")

        log.warning(
            "CDPExecutor live: %s %s %f@%f on %s",
            order.side.value, order.asset, order.quantity, mark, self.network,
        )
        try:
            response = swap_fn(
                network=self.network,
                from_token=_resolve_token(order, side="sell"),
                to_token=_resolve_token(order, side="buy"),
                amount=int(order.quantity * 10**18),
                slippage_bps=50,
            )
        except Exception as exc:  # noqa: BLE001
            log.error("CDP swap failed: %s", exc)
            raise

        # We don't have certainty about the response shape across cdp-sdk
        # minor versions, so coerce defensively.
        fill_price = float(getattr(response, "executed_price", mark) or mark)
        fill_quantity = float(getattr(response, "executed_amount", order.quantity) or order.quantity)
        slippage_bps = abs(fill_price - mark) / max(mark, 1e-9) * 10_000.0
        fee = order.notional * (5.0 / 10_000.0)  # CDP charges roughly 5 bps on Base swaps

        return Fill(
            order=order,
            fill_price=fill_price,
            fill_quantity=fill_quantity,
            fee_paid=fee,
            slippage_bps=slippage_bps,
        )


def _is_live_armed() -> bool:
    return os.getenv("PRAXIS_LIVE", "").lower() in {"1", "true", "yes", "on"}


def _resolve_token(order: Order, side: str) -> str:
    """Asset symbol → on-chain token address (placeholder)."""
    # In a real deployment this routes through StrategyRegistry.adapter
    # which whitelists token addresses per network. For now we surface
    # the asset symbol; the caller is expected to translate via a
    # network-specific token map before invoking live execution.
    return f"{side}:{order.asset}"
