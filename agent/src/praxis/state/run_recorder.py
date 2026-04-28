from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from praxis.state.audit_log import AuditLog


class RunRecorder:
    """Per-run dump:

        runs/<timestamp>_<config_hash>/
            config.yaml
            decisions.jsonl
            equity_curve.csv
            trades.csv
            metrics.json
            report.html  (optional, written by backtest.report)

    The directory name encodes a hash of the config, so re-running the same
    config produces a deterministic suffix and you can tell at a glance which
    runs share inputs.
    """

    def __init__(self, root: str | Path, config_payload: dict[str, Any]) -> None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        cfg_bytes = json.dumps(config_payload, sort_keys=True, default=str).encode()
        config_hash = hashlib.sha256(cfg_bytes).hexdigest()[:8]
        self.dir = Path(root) / f"{ts}_{config_hash}"
        self.dir.mkdir(parents=True, exist_ok=True)
        (self.dir / "config.yaml").write_text(_yaml_dump(config_payload))
        self.audit = AuditLog(self.dir / "decisions.jsonl")

    def save_equity(self, equity: pd.Series) -> None:
        df = equity.rename("equity").to_frame()
        df.index.name = "ts"
        df.to_csv(self.dir / "equity_curve.csv")

    def save_trades(self, trades: pd.DataFrame) -> None:
        trades.to_csv(self.dir / "trades.csv", index=False)

    def save_metrics(self, metrics: dict[str, Any]) -> None:
        (self.dir / "metrics.json").write_text(json.dumps(metrics, indent=2, default=str))

    def close(self) -> None:
        self.audit.close()


def _yaml_dump(payload: dict[str, Any]) -> str:
    try:
        import yaml
        return str(yaml.safe_dump(payload, sort_keys=False, default_flow_style=False))
    except ImportError:
        return json.dumps(payload, indent=2, default=str)
