"""Policy — regime detection + meta-policy that selects strategy weights.

The LLM lives here, and only here. Its job is small: given a regime label
and recent signal stats, output a mapping {strategy_name: weight}. Trading
decisions remain numerical (the strategy/risk layers); the LLM provides
adaptive composition only.
"""
from praxis.policy.meta_policy import MetaPolicy, RuleBasedPolicy
from praxis.policy.regime_detector import RegimeDetector

__all__ = ["RegimeDetector", "MetaPolicy", "RuleBasedPolicy"]
