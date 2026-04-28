"""Run-config loader — every backtest and paper-trade session is described by one YAML."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class RiskConfig:
    max_drawdown: float = 0.25
    per_asset_cap: float = 0.30
    gross_cap: float = 2.0
    net_cap: float = 1.5
    kelly_fraction: float = 0.25


@dataclass
class BacktestConfig:
    name: str
    strategy: str
    universe: list[str]
    start: str
    end: str
    initial_cash: float = 1_000_000.0
    rebalance: str = "1D"
    seed: int = 42
    fee_bps: float = 5.0
    slippage_bps: float = 10.0
    strategy_params: dict[str, Any] = field(default_factory=dict)
    risk: RiskConfig = field(default_factory=RiskConfig)


def load(path: str | Path) -> BacktestConfig:
    raw = yaml.safe_load(Path(path).read_text())
    risk = RiskConfig(**raw.pop("risk", {}))
    return BacktestConfig(risk=risk, **raw)


def dump(cfg: BacktestConfig, path: str | Path) -> None:
    payload = {
        "name": cfg.name,
        "strategy": cfg.strategy,
        "universe": cfg.universe,
        "start": cfg.start,
        "end": cfg.end,
        "initial_cash": cfg.initial_cash,
        "rebalance": cfg.rebalance,
        "seed": cfg.seed,
        "fee_bps": cfg.fee_bps,
        "slippage_bps": cfg.slippage_bps,
        "strategy_params": cfg.strategy_params,
        "risk": cfg.risk.__dict__,
    }
    Path(path).write_text(yaml.safe_dump(payload, sort_keys=False))
