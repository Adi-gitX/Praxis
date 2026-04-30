"""Hypothesis review layer — multi-perspective LLM critique of a hypothesis
*before* it is registered and run.

The architectural principle stays the same: the LLM never trades. Here it
plays a role it is genuinely good at — arguing about hypotheses. Three
personas review a candidate hypothesis from different angles:

* **Skeptic** — argues why the hypothesis will fail.
* **Methodologist** — checks the cross-validation scheme + cost model.
* **Statistician** — checks the trial-count discipline and DSR threshold.

A synthesizer node combines the three critiques into a single recommendation
(*proceed* / *revise* / *reject*) with concrete suggestions. The output is
written to `research/H##_review.md` alongside the notebook.

This pattern is the *only* element of the original blockchAIn codebase that
has been adapted into Praxis: the multi-persona LangGraph idea, repurposed
from "trading agents" (anti-pattern) into "hypothesis devil's advocates"
(reinforcing the deflation discipline).
"""
from praxis.review.graph import HypothesisReview, ReviewResult, run_review
from praxis.review.personas import PERSONAS, Persona

__all__ = ["HypothesisReview", "ReviewResult", "run_review", "Persona", "PERSONAS"]
