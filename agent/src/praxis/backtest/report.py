"""Single-page HTML report — equity curve + drawdown + metrics table.

We deliberately use only the standard library + pandas to render. No matplotlib
dependency: the chart is an inline SVG drawn from the equity series. This means
the report renders identically on any machine and is checked-in friendly.
"""
from __future__ import annotations

from dataclasses import asdict
from html import escape
from pathlib import Path

import pandas as pd

from praxis.backtest.metrics import Metrics


def _normalize(values: list[float]) -> list[float]:
    lo, hi = min(values), max(values)
    span = hi - lo if hi > lo else 1.0
    return [(v - lo) / span for v in values]


def _polyline(equity: pd.Series, width: int, height: int, color: str = "#00ff88") -> str:
    if equity.empty:
        return ""
    values = list(equity.astype(float))
    norm = _normalize(values)
    n = len(values)
    pts = " ".join(
        f"{i * (width / max(n - 1, 1)):.2f},{height - h * height:.2f}" for i, h in enumerate(norm)
    )
    return f'<polyline fill="none" stroke="{color}" stroke-width="2" points="{pts}" />'


def _drawdown_polyline(equity: pd.Series, width: int, height: int) -> str:
    if equity.empty:
        return ""
    cum = equity / equity.iloc[0]
    peak = cum.cummax()
    dd = (cum / peak - 1.0).fillna(0.0)
    values = list(dd.astype(float))
    n = len(values)
    pts = " ".join(
        f"{i * (width / max(n - 1, 1)):.2f},{(-v) * height:.2f}" for i, v in enumerate(values)
    )
    return f'<polyline fill="none" stroke="#ff3366" stroke-width="1.5" stroke-dasharray="4 2" points="{pts}" />'


def write_html_report(
    out_path: str | Path,
    name: str,
    metrics: Metrics,
    equity: pd.Series,
    trades: pd.DataFrame,
    config_summary: dict[str, str] | None = None,
) -> Path:
    out_path = Path(out_path)
    width, height = 880, 240

    rows = "".join(
        f"<tr><td>{escape(k)}</td><td class='num'>{v:.4f}</td></tr>"
        for k, v in asdict(metrics).items()
        if isinstance(v, (int, float))
    )
    cfg_rows = ""
    if config_summary:
        cfg_rows = "".join(
            f"<tr><td>{escape(k)}</td><td>{escape(str(v))}</td></tr>"
            for k, v in config_summary.items()
        )

    trade_count = len(trades) if isinstance(trades, pd.DataFrame) else 0
    equity_svg = _polyline(equity, width, height)
    dd_svg = _drawdown_polyline(equity, width, 120)

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>praxis · {escape(name)}</title>
  <style>
    body {{
      background: #0a0a0a; color: #e5e5e5;
      font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
      margin: 0; padding: 32px;
    }}
    h1 {{ font-weight: 500; letter-spacing: 0.02em; margin: 0 0 4px; }}
    h1 small {{ color: #6b7280; font-weight: 400; margin-left: 12px; }}
    .grid {{ display: grid; grid-template-columns: 2fr 1fr; gap: 24px; margin-top: 24px; }}
    .card {{ border: 1px solid #1f1f1f; padding: 16px; }}
    .card h2 {{ font-size: 0.8rem; color: #6b7280; text-transform: uppercase;
                letter-spacing: 0.1em; margin: 0 0 12px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
    td {{ padding: 4px 0; border-bottom: 1px solid #1a1a1a; }}
    td.num {{ text-align: right; color: #00ff88; }}
    svg {{ display: block; }}
    .axis {{ stroke: #1f1f1f; }}
    .footer {{ margin-top: 32px; color: #6b7280; font-size: 0.75rem; }}
  </style>
</head>
<body>
  <h1>praxis <small>{escape(name)}</small></h1>
  <div class="grid">
    <div class="card">
      <h2>equity curve · drawdown overlay</h2>
      <svg viewBox="0 0 {width} {height}" width="100%">
        <line x1="0" y1="{height}" x2="{width}" y2="{height}" class="axis" />
        {equity_svg}
      </svg>
      <svg viewBox="0 0 {width} 120" width="100%">
        <line x1="0" y1="0" x2="{width}" y2="0" class="axis" />
        {dd_svg}
      </svg>
    </div>
    <div class="card">
      <h2>metrics</h2>
      <table>{rows}</table>
    </div>
  </div>
  <div class="grid">
    <div class="card">
      <h2>config</h2>
      <table>{cfg_rows}</table>
    </div>
    <div class="card">
      <h2>trades</h2>
      <p>n = {trade_count}</p>
    </div>
  </div>
  <p class="footer">praxis · theory becomes execution</p>
</body>
</html>
"""
    out_path.write_text(html)
    return out_path
