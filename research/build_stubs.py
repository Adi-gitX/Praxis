"""Generate empty (pre-registered) notebook stubs for the active hypotheses.

A stub is a notebook that contains the hypothesis statement and the verdict
template, but no executed cells. Pre-registration discipline: the stub
exists *before* the run, so the trial-count for the Deflated Sharpe
penalty is honest.

Run:
    python research/build_stubs.py
"""
from __future__ import annotations

from pathlib import Path

import nbformat as nbf


HYPOTHESES = {
    "H01_momentum_top4_daily": {
        "title": "H01 — Time-series momentum, daily, top-4 majors",
        "statement": (
            "A 60-day momentum signal sized by inverse 30-day vol, applied to "
            "the four crypto majors (BTC, ETH, SOL, AVAX), generates a deflated "
            "Sharpe > 0.5 over 2024 after 5 bps fees and a linear-impact "
            "slippage model."
        ),
        "data": "Binance daily klines (BTC/ETH/SOL/AVAX), 2024-01-01 to 2024-12-31, via ccxt.",
        "method": (
            "Compute log-momentum over 60 days; size inversely to 30-day "
            "realized vol; rebalance daily; cap each leg at 50% of NAV; "
            "apply 5 bps/side and a base 5 bps + linear-impact slippage."
        ),
    },
    "H02_btc_eth_stat_arb": {
        "title": "H02 — BTC/ETH stat-arb log-spread mean-reversion",
        "statement": (
            "The log-spread between BTC and ETH (with online-OLS beta over "
            "60-day rolling window) generates a deflated Sharpe > 0.3 with "
            "z-entry 2.0 / z-exit 0.5 over 2024, after 10 bps/side."
        ),
        "data": "Binance daily klines for BTC/USDT and ETH/USDT, 2024-01-01 to 2024-12-31.",
        "method": (
            "Fit beta by rolling cov/var over 60 days; spread = log(BTC) - "
            "beta * log(ETH); enter when |z| > 2.0, exit when |z| < 0.5; "
            "equal-weight legs at target_weight=0.5; 10 bps/side."
        ),
    },
    "H03_hmm_conditional_voltarget": {
        "title": "H03 — HMM-conditional vol-target outperforms unconditional vol-target",
        "statement": (
            "A vol-target sleeve activated only when the HMM-decoded regime "
            "is RANGING (low-vol state) outperforms an unconditional "
            "vol-target sleeve on Sharpe and Calmar over 2024, after 5 bps/side."
        ),
        "data": "Binance daily klines for BTC/ETH/SOL/AVAX, 2024-01-01 to 2024-12-31.",
        "method": (
            "Fit 2-state Gaussian HMM on (log-return, 30-day realized vol); "
            "compare a vol-target sleeve scaled to 20% annualized portfolio "
            "vol that only allocates in the low-vol state vs. an "
            "unconditional baseline."
        ),
    },
    "H04_drawdown_circuit_breaker_cost": {
        "title": "H04 — Drawdown circuit-breaker is non-negative cost",
        "statement": (
            "Under realistic transaction costs, hard-stopping the strategy "
            "at a 25% peak-to-trough drawdown does not reduce annualized "
            "return by more than 100 bps over a representative bull/bear "
            "cycle (2022-2025)."
        ),
        "data": "Binance daily BTC/USDT, 2022-01-01 to 2025-12-31 (cycle covers two regimes).",
        "method": (
            "Run trend_following with and without the 25% drawdown halt; "
            "compute annualized return delta; report bootstrap CI on the "
            "delta with block=20."
        ),
    },
    "H06_funding_basis_carry": {
        "title": "H06 — Funding-basis carry on Hyperliquid",
        "statement": (
            "Long-spot / short-perp delta-neutral capture on BTC produces a "
            "positive Sharpe after funding payments and 10 bps/side fees in "
            "regimes where annualized funding > 8%."
        ),
        "data": "Binance spot BTC/USDT + Hyperliquid BTC perp funding, hourly, last 12 months.",
        "method": (
            "Long 1× spot, short 1× perp; collect funding; only enter when "
            "trailing 24h funding annualized > 8%; exit when < 4%; 10 bps/"
            "side on entry/exit; PSR/DSR with N=6."
        ),
        "implementation_note": (
            "Hyperliquid perp data requires the Hyperliquid SDK (v0.2 "
            "roadmap item). This stub is the pre-registration; the run "
            "lands when the loader is wired."
        ),
    },
}


def build(slug: str, spec: dict) -> nbf.NotebookNode:
    nb = nbf.v4.new_notebook()
    cells = [
        nbf.v4.new_markdown_cell(f"# {spec['title']}\n\n*Pre-registered. Not yet executed.*"),
        nbf.v4.new_markdown_cell(
            "## Hypothesis\n\n"
            f"{spec['statement']}\n\n"
            "## Data\n\n"
            f"{spec['data']}\n\n"
            "## Method\n\n"
            f"{spec['method']}\n\n"
            + (
                f"## Implementation note\n\n{spec['implementation_note']}\n\n"
                if "implementation_note" in spec
                else ""
            )
            + "## Verdict logic (committed up-front)\n\n"
            "Accept iff the deflated Sharpe ratio (DSR) computed against the "
            "headline OOS returns is ≥ the threshold in the hypothesis "
            "statement, AND the lower bound of a 10,000-iter block-bootstrap "
            "95% CI on Sharpe is > 0.\n\n"
            "Reject iff Sharpe ≤ 0 or DSR < 0.05.\n\n"
            "Otherwise: inconclusive."
        ),
        nbf.v4.new_code_cell(
            "# === DO NOT REMOVE ===\n"
            "# Pre-registration cell. The full pipeline is implemented when this\n"
            "# hypothesis is queued for execution; until then the cells below are\n"
            "# scaffolding only and the verdict prints UNEXECUTED.\n\n"
            "import sys\n"
            "from pathlib import Path\n\n"
            "sys.path.insert(0, str(Path.cwd().parent / 'agent' / 'src'))\n"
            "print('hypothesis registered:', __doc__ if False else 'see markdown above')"
        ),
        nbf.v4.new_markdown_cell(
            "## TODO — fill in before running\n\n"
            "1. Pull data via `praxis.data.ccxt_binance.BinanceLoader` (or the "
            "Hyperliquid loader for H06).\n"
            "2. Compute features `.shift(1)`-safe.\n"
            "3. Build the sleeve as specified in *Method*.\n"
            "4. Apply costs.\n"
            "5. Run `PurgedKFold(k=5, label_horizon=N, embargo_pct=0.01)`.\n"
            "6. Compute `probabilistic_sharpe`, `deflated_sharpe(n_trials=6)`, "
            "and `block_bootstrap_ci`.\n"
            "7. Print verdict via the deterministic logic above.\n"
            "8. Move this row from `Active` to `Completed` in `docs/HYPOTHESES.md` "
            "with the verdict + numbers."
        ),
        nbf.v4.new_code_cell(
            "verdict = 'UNEXECUTED'\n"
            "print('=' * 72)\n"
            "print(f'  verdict:  {verdict}')\n"
            "print('=' * 72)"
        ),
    ]
    nb.cells = cells
    nb.metadata.update(
        {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.11"},
        }
    )
    return nb


OUT_DIR = Path(__file__).parent
for slug, spec in HYPOTHESES.items():
    path = OUT_DIR / f"{slug}.ipynb"
    if path.exists():
        print(f"skip  (exists)   {path.name}")
        continue
    nb = build(slug, spec)
    nbf.write(nb, path)
    print(f"wrote            {path.name}")
