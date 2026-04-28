"""Execution — converts approved orders into either simulated fills (paper)
or on-chain swaps (CDP). Orders are received post-risk-gate; this layer never
re-checks risk.
"""
from praxis.execution.cdp_executor import CDPExecutor, PaperExecutor
from praxis.execution.slippage import LinearImpact, estimate_slippage_bps

__all__ = ["PaperExecutor", "CDPExecutor", "LinearImpact", "estimate_slippage_bps"]
