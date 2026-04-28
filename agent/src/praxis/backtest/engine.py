from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import pandas as pd

from praxis.execution.cdp_executor import Fill, PaperExecutor
from praxis.policy.meta_policy import MetaPolicy, RuleBasedPolicy
from praxis.policy.regime_detector import RegimeDetector
from praxis.risk.gate import RiskGate
from praxis.signals.base import Signal
from praxis.state.run_recorder import RunRecorder
from praxis.strategies.base import Strategy
from praxis.types import Decision, Order, PortfolioState, Side


@dataclass
class BacktestResult:
    equity_curve: pd.Series
    trades: pd.DataFrame
    decisions: list[Decision] = field(default_factory=list)
    fills: list[Fill] = field(default_factory=list)
    final_portfolio: PortfolioState | None = None


class BacktestEngine:
    """Event-driven backtest loop.

    For each rebalance bar:
        1. Compute all required signals (cached across strategies sharing them).
        2. RegimeDetector classifies the current regime.
        3. MetaPolicy weights the active strategies.
        4. Each strategy emits target weights; engine combines to a portfolio target.
        5. Translate weight delta into orders (buy/sell to reach target notional).
        6. RiskGate checks each order; rejected orders are dropped, partials trimmed.
        7. PaperExecutor applies fills with slippage + fees.
        8. Equity is marked-to-market and recorded.

    Strict no-lookahead: signals are computed once over the full window, but at
    each step we only read `signals.loc[ts]` — strategies are forbidden from
    indexing beyond `ts` (the abstract base contract documents this).
    """

    def __init__(
        self,
        prices: pd.DataFrame,
        strategies: list[Strategy],
        risk_gate: RiskGate | None = None,
        meta_policy: MetaPolicy | None = None,
        regime_detector: RegimeDetector | None = None,
        executor: PaperExecutor | None = None,
        initial_cash: float = 1_000_000.0,
        rebalance_every: int = 1,
        liquidity_per_asset: float | dict[str, float] = 50_000_000.0,
        run_recorder: RunRecorder | None = None,
    ) -> None:
        self.prices = prices
        self.strategies = strategies
        self.strategy_index = {s.name: s for s in strategies}
        self.risk_gate = risk_gate or RiskGate()
        self.meta_policy = meta_policy or RuleBasedPolicy()
        self.regime_detector = regime_detector or RegimeDetector()
        self.executor = executor or PaperExecutor()
        self.initial_cash = initial_cash
        self.rebalance_every = rebalance_every
        self.liquidity = (
            liquidity_per_asset
            if isinstance(liquidity_per_asset, dict)
            else {a: liquidity_per_asset for a in prices.columns}
        )
        self.run_recorder = run_recorder

    def _compute_signals(self) -> dict[str, pd.DataFrame]:
        unique: dict[str, Signal] = {}
        for strat in self.strategies:
            for sig in strat.required_signals():
                unique.setdefault(sig.spec.name, sig)
        return {name: sig.compute(self.prices) for name, sig in unique.items()}

    def _orders_for_target(
        self,
        ts: pd.Timestamp,
        target_weights: dict[str, float],
        portfolio: PortfolioState,
        marks: dict[str, float],
        strategy_name: str,
    ) -> list[Order]:
        nav = portfolio.equity(marks)
        orders: list[Order] = []
        for asset, weight in target_weights.items():
            if not math.isfinite(weight):
                continue
            mark = marks.get(asset)
            if mark is None or mark <= 0:
                continue
            target_notional = weight * nav
            existing = portfolio.positions.get(asset)
            existing_notional = existing.quantity * mark if existing else 0.0
            delta_notional = target_notional - existing_notional
            if abs(delta_notional) < max(1.0, 0.0005 * nav):  # ignore <5bps NAV jitter
                continue
            qty = abs(delta_notional) / mark
            side = Side.BUY if delta_notional > 0 else Side.SELL
            orders.append(
                Order(
                    asset=asset,
                    side=side,
                    quantity=qty,
                    notional=abs(delta_notional),
                    ts=ts.to_pydatetime() if hasattr(ts, "to_pydatetime") else ts,
                    strategy=strategy_name,
                    rationale={"target_weight": float(weight), "delta_notional": float(delta_notional)},
                )
            )
        return orders

    def run(self) -> BacktestResult:
        signals = self._compute_signals()
        warmup = max((s.warmup() for s in self.strategies), default=0)

        portfolio = PortfolioState(cash=self.initial_cash)
        equity_records: list[tuple[datetime, float]] = []
        decisions: list[Decision] = []
        trade_rows: list[dict[str, Any]] = []

        timestamps = self.prices.index
        for i, ts in enumerate(timestamps):
            marks = self.prices.loc[ts].to_dict()
            equity = portfolio.equity(marks)
            equity_records.append((ts.to_pydatetime() if hasattr(ts, "to_pydatetime") else ts, equity))

            if i < warmup or i % self.rebalance_every != 0:
                continue

            regime = self.regime_detector.classify(self.prices.iloc[: i + 1])
            strat_weights_meta = self.meta_policy.select(regime, signal_summary={})

            combined_target: dict[str, float] = {}
            attribution_log: dict[str, float] = {}
            signal_log: dict[str, float] = {}
            for strat in self.strategies:
                meta_w = strat_weights_meta.get(strat.name, 0.0)
                if meta_w <= 0:
                    continue
                output = strat.step(ts, self.prices.iloc[: i + 1], signals)
                for asset, w in output.target_weights.items():
                    combined_target[asset] = combined_target.get(asset, 0.0) + meta_w * w
                signal_log.update(output.signal_snapshot)
                for asset, contrib in output.attribution.items():
                    attribution_log[f"{strat.name}.{asset}"] = float(meta_w * contrib)

            orders = self._orders_for_target(ts, combined_target, portfolio, marks, "+".join(self.strategy_index))
            checks = []
            executed_fills = []
            for order in orders:
                check = self.risk_gate.check(order, portfolio, marks)
                checks.append(check)
                if not check.approved:
                    continue
                final_qty = check.adjusted_quantity if check.adjusted_quantity is not None else order.quantity
                if final_qty <= 0:
                    continue
                exec_order = Order(
                    asset=order.asset,
                    side=order.side,
                    quantity=final_qty,
                    notional=final_qty * marks[order.asset],
                    ts=order.ts,
                    strategy=order.strategy,
                    rationale=order.rationale,
                )
                fill = self.executor.execute(exec_order, marks[order.asset], self.liquidity.get(order.asset, 1e9))
                if fill is None:
                    continue
                executed_fills.append(fill)
                cash_delta = self.executor.apply_fill(portfolio.positions, fill)
                portfolio.cash += cash_delta
                trade_rows.append(
                    {
                        "ts": fill.order.ts,
                        "asset": fill.order.asset,
                        "side": fill.order.side.value,
                        "quantity": fill.fill_quantity,
                        "fill_price": fill.fill_price,
                        "fee": fill.fee_paid,
                        "slippage_bps": fill.slippage_bps,
                        "strategy": fill.order.strategy,
                    }
                )

            decision = Decision(
                ts=ts.to_pydatetime() if hasattr(ts, "to_pydatetime") else ts,
                regime=regime,
                signals=signal_log,
                target_weights=combined_target,
                orders=orders,
                risk_checks=checks,
                notes=f"meta_weights={strat_weights_meta} attribution={attribution_log}",
            )
            decisions.append(decision)
            if self.run_recorder is not None:
                self.run_recorder.audit.write(decision)

        equity_index, equity_values = zip(*equity_records) if equity_records else ((), ())
        equity_series = pd.Series(equity_values, index=pd.to_datetime(list(equity_index)), name="equity")
        trades_df = pd.DataFrame(trade_rows)
        return BacktestResult(
            equity_curve=equity_series,
            trades=trades_df,
            decisions=decisions,
            fills=list(self.executor.fills),
            final_portfolio=portfolio,
        )
