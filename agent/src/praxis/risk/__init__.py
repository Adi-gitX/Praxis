"""Risk — every order passes through `RiskGate.check` before execution.

This is the single most important module in Praxis. The original-author
codebase had no risk layer at all — orders went directly from LLM to wallet.
Here, we enforce three independent checks (Kelly sizing, drawdown, exposure),
and the gate is the single chokepoint between policy and execution.
"""
from praxis.risk.drawdown import DrawdownMonitor
from praxis.risk.exposure import ExposureLimits
from praxis.risk.gate import RiskGate
from praxis.risk.kelly import fractional_kelly

__all__ = ["RiskGate", "DrawdownMonitor", "ExposureLimits", "fractional_kelly"]
