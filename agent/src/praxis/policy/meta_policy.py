"""Meta-policy: regime -> strategy weights.

Two implementations share the same interface:

* `RuleBasedPolicy` — deterministic mapping. Always available, zero deps.
* `LLMMetaPolicy`   — LangGraph state machine that calls an LLM to propose
                      weights given regime + signal summary. Falls back to
                      `RuleBasedPolicy` if no `OPENAI_API_KEY` is set or the
                      LLM call errors. This keeps the demo runnable end-to-end
                      without external keys.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Protocol

from praxis.types import Regime

log = logging.getLogger(__name__)


class MetaPolicy(Protocol):
    def select(self, regime: Regime, signal_summary: dict[str, float]) -> dict[str, float]: ...


_DEFAULT_TABLE: dict[Regime, dict[str, float]] = {
    Regime.TRENDING: {"trend_following": 1.0, "stat_arb": 0.0, "vol_target": 0.0},
    Regime.RANGING: {"trend_following": 0.0, "stat_arb": 0.7, "vol_target": 0.3},
    Regime.HIGH_VOL: {"trend_following": 0.3, "stat_arb": 0.2, "vol_target": 0.5},
    Regime.CRISIS: {"trend_following": 0.0, "stat_arb": 0.0, "vol_target": 0.0},
}


@dataclass
class RuleBasedPolicy:
    """Deterministic regime -> strategy weights table.

    The table is editable; this is the baseline against which any LLM policy
    must demonstrate improvement in backtest.
    """

    table: dict[Regime, dict[str, float]] = field(default_factory=lambda: dict(_DEFAULT_TABLE))

    def select(self, regime: Regime, signal_summary: dict[str, float]) -> dict[str, float]:
        return dict(self.table[regime])


class LLMMetaPolicy:
    """LangGraph wrapper that asks an LLM to weight strategies given the regime.

    The graph is a single node that produces strict-JSON weights. We validate
    the JSON, normalise to sum<=1, and clip to [0, 1]. Anything malformed
    falls back to the rule-based policy.
    """

    def __init__(self, model: str = "gpt-4o-mini", strategies: list[str] | None = None) -> None:
        self.model = model
        self.strategies = strategies or ["trend_following", "stat_arb", "vol_target"]
        self._fallback = RuleBasedPolicy()
        self._enabled = bool(os.getenv("OPENAI_API_KEY"))
        self._graph: object | None = self._build_graph() if self._enabled else None

    def _build_graph(self) -> object | None:
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            from langchain_openai import ChatOpenAI
            from langgraph.graph import END, StateGraph
        except ImportError:
            log.warning("LangGraph/LangChain not installed; LLMMetaPolicy disabled.")
            self._enabled = False
            return None

        from typing import TypedDict

        class State(TypedDict):
            regime: str
            signals: dict[str, float]
            weights: dict[str, float]

        llm = ChatOpenAI(model=self.model, temperature=0.0)

        def propose(state: State) -> State:
            sys = SystemMessage(
                content=(
                    "You are a quant strategist allocating between fixed strategies. "
                    f"Strategies: {self.strategies}. Output strict JSON of the form "
                    '{"trend_following": 0.5, "stat_arb": 0.3, "vol_target": 0.2}. '
                    "Weights must be in [0, 1] and sum to <= 1.0. No prose."
                )
            )
            user = HumanMessage(
                content=json.dumps(
                    {"regime": state["regime"], "signal_summary": state["signals"]}
                )
            )
            response = llm.invoke([sys, user])
            text = response.content if isinstance(response.content, str) else str(response.content)
            try:
                weights = json.loads(text)
            except json.JSONDecodeError:
                weights = {}
            return {**state, "weights": weights}

        graph = StateGraph(State)
        graph.add_node("propose", propose)
        graph.set_entry_point("propose")
        graph.add_edge("propose", END)
        return graph.compile()

    def select(self, regime: Regime, signal_summary: dict[str, float]) -> dict[str, float]:
        graph = self._graph
        if not self._enabled or graph is None:
            return self._fallback.select(regime, signal_summary)
        try:
            out = graph.invoke(  # type: ignore[attr-defined]
                {"regime": regime.value, "signals": signal_summary, "weights": {}}
            )
            weights = out.get("weights") or {}
            cleaned = {
                s: max(0.0, min(1.0, float(weights.get(s, 0.0)))) for s in self.strategies
            }
            total = sum(cleaned.values())
            if total > 1.0:
                cleaned = {s: w / total for s, w in cleaned.items()}
            return cleaned
        except Exception as exc:  # noqa: BLE001
            log.warning("LLMMetaPolicy fell back to rule-based: %s", exc)
            return self._fallback.select(regime, signal_summary)
