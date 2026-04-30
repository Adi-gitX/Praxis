# Loom Walkthrough Script · 2 minutes 30 seconds

A tight tour for a quant recruiter. Designed to play in one take — every
beat is an artifact already in the repo, no slides, no editing.

---

## 0:00 — 0:25 · Hook (one screen, one number)

**On screen:** [http://localhost:3000](http://localhost:3000) (the landing page).

**Say:**

> *"Praxis is a research framework for autonomous quantitative trading on
> on-chain markets. The headline result is here — H05, a hidden-Markov
> regime-conditional momentum sleeve on 17,000 hours of BTCUSDT, evaluated
> end-to-end. Net Sharpe of negative two point four. The pipeline rejects
> it. That's the contribution: a framework where a clean negative is
> trustworthy."*

Cursor lands on the headline metrics row. Don't dwell — move.

## 0:25 — 1:00 · The architecture, in one glance

**On screen:** scroll to the mermaid diagram in `README.md` on GitHub
(or the architecture card stack on the landing page if pre-deploy).

**Say:**

> *"Six layers — signals, strategies, regime, risk gate, execution,
> on-chain. The LLM lives only in the policy layer; it weights strategies
> given the regime. It never picks signals, never sizes positions, never
> sends a transaction. Trade generation is deterministic numerical code.
> Every order passes through a single risk gate before execution: Kelly
> sizing, drawdown circuit-breaker, exposure caps. There's no execution
> path that bypasses it."*

## 1:00 — 1:40 · The one notebook

**On screen:** `research/H05_hmm_volatility_regime.ipynb` opened in
GitHub or VS Code. Scroll to the verdict cell at the bottom.

**Say:**

> *"H05 is pre-registered. The hypothesis statement, the verdict logic,
> and the deflation count are all committed before the cells run. The
> notebook fits a 2-state Gaussian HMM on log-returns and 24-hour realized
> vol, builds a momentum z-score sleeve, applies 10 basis points per side,
> validates with Purged K-Fold cross-validation following López de Prado.
> The Deflated Sharpe under N equals six trials is zero. The 95-percent
> bootstrap confidence interval is entirely below zero. The verdict cell
> prints 'does NOT survive deflation.' I report it as-is — that's what a
> recruiter should see."*

## 1:40 — 2:10 · The risk gate is real

**On screen:** [http://localhost:3000/risk](http://localhost:3000/risk).

**Say:**

> *"On-chain, the killswitch is timelocked. A guardian role can halt the
> vault instantly; unhalting requires the admin to schedule it and wait
> 24 hours. The vault is ERC-4626 with a strategy registry, a risk
> oracle, and four primitives total. Solidity 0.8.27 with cancun, OZ v5,
> Hardhat tests pass two of two. Off-chain, the same drawdown logic
> runs as a Python circuit-breaker — one-way trip at 25 percent
> peak-to-trough. Every order that breaches a per-asset cap gets
> partially trimmed, every order that breaches gross or net leverage
> gets rejected."*

## 2:10 — 2:30 · Reproducibility

**On screen:** terminal showing `git log --oneline | head -8` and the
`runs/20260430T122652Z_aed954c8/` directory.

**Say:**

> *"Every backtest dumps a config, a JSONL audit log, an equity curve,
> a trades file, metrics, and a one-page HTML tearsheet. The directory
> name is a hash of the config, so two runs with the same inputs share
> a suffix and are trivially diffable. Clone, run `poetry install`,
> run one command — you reproduce the H05 verdict in five minutes.
> Whitepaper is in `docs/WHITEPAPER.pdf`, four pages. That's Praxis."*

End frame: the GitHub repo URL.

---

## Production tips

- **Record at 1440p.** The terminal text is dense; readability matters.
- **Two takes max.** If a beat doesn't land, re-record only that segment.
  Don't try to perfect it.
- **Don't apologize for the negative result.** It's the strongest signal
  — most candidates fake equity curves; you didn't.
- **Cut the music.** Quant recruiters watch on mute at 1.25×.

## File checklist before you record

```bash
# pin the dev server
cd app && npm run dev          # http://localhost:3000

# open these tabs
# 1. http://localhost:3000           (landing)
# 2. http://localhost:3000/risk      (risk dashboard)
# 3. github.com/Adi-gitX/Praxis      (post-push)
# 4. github.com/Adi-gitX/Praxis/blob/main/research/H05_hmm_volatility_regime.ipynb
# 5. github.com/Adi-gitX/Praxis/blob/main/docs/WHITEPAPER.pdf

# have these in the terminal
git log --oneline | head -8
ls runs/20260430T122652Z_aed954c8/
```
