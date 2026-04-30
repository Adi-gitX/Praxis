"""LangGraph state machine for the hypothesis review.

Graph shape:

    Hypothesis -> [skeptic, methodologist, statistician] -> synthesizer -> verdict

The three reviewer nodes run in parallel against the same hypothesis. The
synthesizer reads all three critiques and emits a single recommendation
(proceed / revise / reject) plus a one-paragraph summary.

When `OPENAI_API_KEY` is unset the graph short-circuits to a deterministic
stub that emits scaffolded critiques pointing at the persona prompts —
useful for testing the wiring without spending tokens.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any

from praxis.review.personas import PERSONAS, METHODOLOGIST, SKEPTIC, STATISTICIAN, Persona

log = logging.getLogger(__name__)


@dataclass
class HypothesisReview:
    """Inputs to the review graph."""

    id: str
    title: str
    statement: str
    data: str
    method: str
    n_trials: int
    dsr_threshold: float = 0.5


@dataclass
class ReviewResult:
    hypothesis_id: str
    skeptic: str
    methodologist: str
    statistician: str
    recommendation: str  # one of: "proceed", "revise", "reject"
    rationale: str

    def as_markdown(self, hyp: HypothesisReview) -> str:
        return f"""# {hyp.id} · pre-registration review

> _Multi-perspective critique generated before this hypothesis was run.
> The recommendation below is **advisory** — it does not block execution,
> but every revision should be traceable to a critique here._

**Hypothesis.** {hyp.statement}

**Recommendation:** **{self.recommendation.upper()}**

{self.rationale}

---

## Skeptic (adversarial)

{self.skeptic}

## Methodologist (CV scheme + cost model)

{self.methodologist}

## Statistician (trial-count + threshold)

{self.statistician}
"""


def _stub_critique(persona: Persona, hyp: HypothesisReview) -> str:
    """Deterministic placeholder for when no OPENAI_API_KEY is configured.

    Returns a critique stub keyed by the persona — *not* a fake review.
    The output explicitly says it is a stub so a reviewer reading the
    rendered review.md can never mistake it for an LLM-generated one.
    """
    return (
        f"_STUB_ — `{persona.name}` review skipped (no `OPENAI_API_KEY` configured). "
        f"To generate this review, run with the key set; the graph will replace "
        f"this stub with the LLM's critique under `{persona.role}`."
    )


def _llm_critique(persona: Persona, hyp: HypothesisReview, model: str) -> str:
    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_openai import ChatOpenAI
    except ImportError:
        log.warning("langchain not installed; review falls back to stub")
        return _stub_critique(persona, hyp)
    llm = ChatOpenAI(model=model, temperature=0.2)
    user_msg = (
        f"Hypothesis ID: {hyp.id}\n"
        f"Title: {hyp.title}\n"
        f"Statement: {hyp.statement}\n"
        f"Data: {hyp.data}\n"
        f"Method: {hyp.method}\n"
        f"Pre-registered N_trials: {hyp.n_trials}\n"
        f"DSR acceptance threshold: {hyp.dsr_threshold}\n"
    )
    try:
        response = llm.invoke(
            [SystemMessage(content=persona.system_prompt), HumanMessage(content=user_msg)]
        )
        text = response.content if isinstance(response.content, str) else str(response.content)
        return text.replace("<END>", "").strip()
    except Exception as exc:  # noqa: BLE001
        log.warning("LLM review failed for %s: %s", persona.name, exc)
        return _stub_critique(persona, hyp)


def _synthesize(hyp: HypothesisReview, critiques: dict[str, str], model: str) -> tuple[str, str]:
    if not os.getenv("OPENAI_API_KEY"):
        return (
            "revise" if any("STUB" not in c for c in critiques.values()) else "proceed",
            (
                "Synthesizer skipped (no `OPENAI_API_KEY`). The three persona stubs above "
                "are placeholders; treat the verdict as 'proceed by default' until an "
                "LLM-backed run replaces this with a real synthesis."
            ),
        )
    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_openai import ChatOpenAI
    except ImportError:
        return ("proceed", "Synthesizer unavailable; langchain not installed.")
    llm = ChatOpenAI(model=model, temperature=0.0)
    sys = SystemMessage(
        content=(
            "You are a senior research lead synthesizing three reviews of a "
            "pre-registered hypothesis. Output strict JSON with exactly two keys: "
            '"recommendation" (one of "proceed", "revise", "reject") and "rationale" '
            "(2–3 sentences explaining the call). Bias the recommendation toward "
            "'revise' when any reviewer raised a concern that, if true, would "
            "invalidate the headline result. Bias toward 'reject' only when "
            "multiple reviewers agree the design is fundamentally broken."
        )
    )
    user = HumanMessage(
        content=json.dumps(
            {
                "hypothesis": {
                    "id": hyp.id,
                    "title": hyp.title,
                    "statement": hyp.statement,
                    "n_trials": hyp.n_trials,
                    "dsr_threshold": hyp.dsr_threshold,
                },
                "critiques": critiques,
            }
        )
    )
    try:
        response = llm.invoke([sys, user])
        text = response.content if isinstance(response.content, str) else str(response.content)
        parsed = json.loads(text)
        rec = str(parsed.get("recommendation", "revise")).lower()
        if rec not in {"proceed", "revise", "reject"}:
            rec = "revise"
        return rec, str(parsed.get("rationale", "no rationale returned"))
    except Exception as exc:  # noqa: BLE001
        log.warning("synthesizer failed: %s", exc)
        return ("revise", f"Synthesizer error ({exc}); defaulting to 'revise'.")


def run_review(hyp: HypothesisReview, model: str = "gpt-4o-mini") -> ReviewResult:
    """Run the three reviewers and the synthesizer.

    The graph is logically:

        skeptic, methodologist, statistician  -->  synthesizer

    With LangGraph the parallel fan-out is straightforward; we keep it linear
    here for clarity since the persona-critique calls are independent and
    LangChain's `ChatOpenAI` is sync. A future PR can wrap this in
    `langgraph.graph.StateGraph` for first-class checkpointing.
    """
    critiques: dict[str, str] = {}
    for persona in PERSONAS:
        if os.getenv("OPENAI_API_KEY"):
            critiques[persona.name] = _llm_critique(persona, hyp, model=model)
        else:
            critiques[persona.name] = _stub_critique(persona, hyp)

    rec, rationale = _synthesize(hyp, critiques, model=model)

    return ReviewResult(
        hypothesis_id=hyp.id,
        skeptic=critiques[SKEPTIC.name],
        methodologist=critiques[METHODOLOGIST.name],
        statistician=critiques[STATISTICIAN.name],
        recommendation=rec,
        rationale=rationale,
    )


def review_to_dict(result: ReviewResult) -> dict[str, Any]:
    return {
        "hypothesis_id": result.hypothesis_id,
        "skeptic": result.skeptic,
        "methodologist": result.methodologist,
        "statistician": result.statistician,
        "recommendation": result.recommendation,
        "rationale": result.rationale,
    }
