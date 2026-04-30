"""Tests for the multi-persona hypothesis review layer.

We never call OpenAI in tests — the review module's stub path is the
contract under test. Real LLM calls are exercised via the CLI in CI when
an OPENAI_API_KEY is present (a future enhancement).
"""
from __future__ import annotations

import pytest

from praxis.review import HypothesisReview, run_review
from praxis.review.personas import METHODOLOGIST, PERSONAS, SKEPTIC, STATISTICIAN


@pytest.fixture
def hyp() -> HypothesisReview:
    return HypothesisReview(
        id="H99",
        title="Test hypothesis",
        statement="A test statement.",
        data="synthetic",
        method="synthetic",
        n_trials=6,
        dsr_threshold=0.5,
    )


def test_personas_are_three_distinct_roles() -> None:
    assert len(PERSONAS) == 3
    names = {p.name for p in PERSONAS}
    assert names == {"skeptic", "methodologist", "statistician"}
    # System prompts are non-trivial
    for p in PERSONAS:
        assert len(p.system_prompt) > 200
        assert "<END>" in p.system_prompt


def test_run_review_stub_path_returns_all_three(monkeypatch: pytest.MonkeyPatch, hyp: HypothesisReview) -> None:
    """Without OPENAI_API_KEY, every persona returns a clearly-labelled stub."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = run_review(hyp)
    assert result.hypothesis_id == "H99"
    for critique in (result.skeptic, result.methodologist, result.statistician):
        assert "STUB" in critique
    assert result.recommendation in {"proceed", "revise", "reject"}
    assert "OPENAI_API_KEY" in result.rationale


def test_review_renders_to_markdown(monkeypatch: pytest.MonkeyPatch, hyp: HypothesisReview) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = run_review(hyp)
    md = result.as_markdown(hyp)
    assert "# H99 · pre-registration review" in md
    assert "Recommendation:" in md
    assert "## Skeptic" in md
    assert "## Methodologist" in md
    assert "## Statistician" in md
    assert hyp.statement in md


def test_persona_singletons_referenced_correctly() -> None:
    assert SKEPTIC.name == "skeptic"
    assert METHODOLOGIST.name == "methodologist"
    assert STATISTICIAN.name == "statistician"
