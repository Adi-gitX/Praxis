---
title: "Praxis: A Reproducible Research Framework for On-Chain Quantitative Trading"
author: "Aditya Kammati"
date: "April 2026"
documentclass: article
geometry: "margin=1in"
fontsize: 11pt
header-includes:
  - \usepackage{microtype}
  - \usepackage{xcolor}
link-citations: true
colorlinks: true
linkcolor: "blue"
urlcolor: "blue"
citecolor: "blue"
references:
  - id: lopezdeprado2018afml
    type: book
    author:
      - family: López de Prado
        given: Marcos
    title: Advances in Financial Machine Learning
    publisher: Wiley
    issued: { year: 2018 }
  - id: bailey2014dsr
    type: article-journal
    author:
      - family: Bailey
        given: David H.
      - family: López de Prado
        given: Marcos
    title: "The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting and Non-Normality"
    container-title: Journal of Portfolio Management
    issued: { year: 2014 }
    volume: 40
    issue: 5
    page: 94-107
  - id: bailey2012psr
    type: article-journal
    author:
      - family: Bailey
        given: David H.
      - family: López de Prado
        given: Marcos
    title: "The Sharpe Ratio Efficient Frontier"
    container-title: Journal of Risk
    issued: { year: 2012 }
    volume: 15
    issue: 2
  - id: bailey2017pbo
    type: article-journal
    author:
      - family: Bailey
        given: David H.
      - family: Borwein
        given: Jonathan
      - family: López de Prado
        given: Marcos
      - family: Zhu
        given: Qiji Jim
    title: "The Probability of Backtest Overfitting"
    container-title: Journal of Computational Finance
    issued: { year: 2017 }
    volume: 20
    issue: 4
    page: 39-69
  - id: daian2020fb2
    type: paper-conference
    author:
      - family: Daian
        given: Philip
      - family: Goldfeder
        given: Steven
      - family: Kell
        given: Tyler
      - family: Li
        given: Yunqi
      - family: Zhao
        given: Xueyuan
      - family: Bentov
        given: Iddo
      - family: Breidenbach
        given: Lorenz
      - family: Juels
        given: Ari
    title: "Flash Boys 2.0: Frontrunning in Decentralized Exchanges, Miner Extractable Value, and Consensus Instability"
    container-title: 2020 IEEE Symposium on Security and Privacy
    issued: { year: 2020 }
    page: 910-927
  - id: grinold2000active
    type: book
    author:
      - family: Grinold
        given: Richard C.
      - family: Kahn
        given: Ronald N.
    title: "Active Portfolio Management"
    publisher: McGraw-Hill
    edition: 2
    issued: { year: 2000 }
  - id: hamilton1989regime
    type: article-journal
    author:
      - family: Hamilton
        given: James D.
    title: "A New Approach to the Economic Analysis of Nonstationary Time Series and the Business Cycle"
    container-title: Econometrica
    issued: { year: 1989 }
    volume: 57
    issue: 2
    page: 357-384
---

## Abstract

Praxis is a research-first framework for autonomous quantitative trading on
on-chain markets. It composes a numerical signal layer, a regime-aware
meta-policy, and a single risk gate; an LLM weights strategies given the
detected regime but never participates in trade generation itself. We
pre-register six hypotheses, run one of them (H05: HMM-conditional momentum
on BTCUSDT 1h, 24 months) end-to-end with a deflated Sharpe of zero, and
report the result honestly. The framework's value lies in the pipeline that
makes such a clean negative possible — purged k-fold CV with embargo
[@lopezdeprado2018afml], probabilistic and deflated Sharpe ratios
[@bailey2012psr; @bailey2014dsr], 10 000-iteration block bootstrap CIs, and
a deterministic config-hashed run recorder. All code, contracts, and the
operator terminal are MIT-licensed.

## 1 Motivation

The first wave of "AI agents with wallets" routed an LLM directly to
on-chain execution. That architecture conflates two distinct decisions:
*what should the position be* (a numerical question that admits rigorous
treatment) and *how should we adapt to the current regime* (a soft pattern
question where LLMs can plausibly help). Praxis splits them: signals and
strategies are deterministic, the LLM weights strategies given a detected
regime, and a single risk gate filters every order. The contribution is
the architecture and the pipeline, not a new alpha.

The benchmark reader is a quantitative researcher screening portfolio
submissions. Their bar is "could a senior quant read this in twenty minutes
and understand what was tested and why?" This paper is that twenty-minute
read.

## 2 Data and Methodology

**Data.** BTCUSDT 1h klines from Binance via `ccxt`, 2024-05-10 →
2026-04-30 (17,281 bars). Candles are cached to parquet on first fetch;
re-runs are deterministic and offline. We use 1h granularity rather than
daily because the deflation penalty grows with sample size and we wanted
at least 10,000 observations per fold.

**Pipeline.** From close prices we construct (i) one-bar log-returns,
(ii) 24h annualized realized volatility (cross-section across one asset
collapses to univariate), and (iii) a 168-bar (one-week) momentum
z-score. A 2-state Gaussian HMM is fit on the (log-return, realized vol)
joint distribution by EM with Viterbi decoding [@hamilton1989regime];
states are ranked by realized volatility post-hoc so labels are stable
across re-fits — state 0 is always the lower-vol regime.

**Sleeve.** `size_t = sign(mom_z_t) · clip(|mom_z_t|/2, 0, 1)`, with the
high-vol regime scaling ×0.25. The signal is shifted by one bar before
being applied, so the position at bar t depends only on data observable at
the close of bar t-1.

**Costs.** 10 bps/side on every change in size — turnover proxy. Generous
for a major-pair venue but tight enough that a real signal must clear it.

**Validation.** Purged K-Fold (k=5, label horizon 168, 1% embargo)
following [@lopezdeprado2018afml] ch. 7. Each fold's Sharpe is computed
only on its held-out window. Probabilistic Sharpe Ratio (PSR) computes
P(true SR > 0) under non-normal returns [@bailey2012psr]; the Deflated
Sharpe Ratio (DSR) penalises selection bias against N=6 trial hypotheses
[@bailey2014dsr], reflecting the six rows pre-registered in the project
`HYPOTHESES.md` before the run. Confidence intervals on the Sharpe come
from a 10 000-iteration block bootstrap with block size 24h, matching the
likely autocorrelation length of hourly returns.

**.shift(1) audit.** Every feature is computed at bar t from data up to
and including bar t. The position derived from those features is then
shifted by one bar (`size = size.shift(1).fillna(0.0)`) before being
multiplied into the bar-t+1 log-return. There is no path in the pipeline
that lets the strategy observe its own contemporaneous label.

## 3 Result

| metric                           | value         |
|----------------------------------|---------------|
| Sharpe (net of 10 bps/side)      | **−2.4238**   |
| 95% CI on Sharpe (block=24, 10k iter) | **[−3.83, −1.01]** |
| Probabilistic Sharpe (vs SR=0)   | **0.0004**    |
| Deflated Sharpe (N=6 trials)     | **0.0000**    |
| Mean OOS Sharpe (PurgedKFold k=5)| **−2.4454**   |
| Final equity (1.0 = breakeven)   | 0.4909        |
| Bars                             | 17,089        |

The verdict, evaluated by deterministic logic committed to the notebook
*before* the cells were run (DSR at least 0.5 and CI low above zero -> accept;
SR at or below zero or DSR below 0.05 -> reject; else inconclusive), is
**rejected: does not survive
deflation**. Net Sharpe is negative even at the point estimate; the entire
95% bootstrap CI lies below zero; OOS folds agree, all five negative; PSR
~ 0 and DSR rounds to zero. Gross Sharpe before fees is −0.41 — the signal
is anti-correlated with forward returns over this window. Adding 10
bps/side amplifies the bleed because the sleeve trades on every change in
the soft-clipped momentum signal.

This is the headline result, reported as-is.

## 4 Limitations

**Single venue, single asset.** We tested one (BTCUSDT) on one venue
(Binance). A negative Sharpe here does not generalize across venues with
different fee schedules (Hyperliquid maker rebates, for instance) nor
across the cross-section of major pairs.

**Single 24-month sample.** The window includes one cycle bottom and one
cycle top. A longer sample (e.g. 2018-present) would let us examine
parameter stability across the 2020-2021 bull, the 2022 bear, and the
2024-2025 cycle. We elected to keep the window short to make the
notebook re-runnable in under five minutes.

**Cost model.** We used a flat 10 bps/side. A more accurate model would
have a base + linear-impact term scaling with size relative to top-of-book
depth, and would distinguish maker from taker fills. Hyperliquid maker
rebates would invert the sign of fee drag for a sufficiently long-only
strategy. We did not implement maker/taker classification because the
result was already conclusive at the cruder cost model.

**No live capital.** The framework supports paper-trading mode end-to-end,
but no live deployment has been run. The CDP executor in `agent/.../
execution/cdp_executor.py` is intentionally `NotImplementedError` until an
operator opts into live trading via an explicit CLI flag.

**MEV-aware execution.** Routing through Flashbots Protect or MEV-Share
would matter for any DEX-side execution [@daian2020fb2], but we did not
test on-chain venues in this run; the result is purely CEX paper.

**Trial count.** We deflated against N=6 trials. If we had searched
parameter space (lookback, regime threshold, sleeve clipping curve) we
would have to inflate N substantially [@bailey2017pbo] and the headline
result would be even less significant. Conversely, if we revisit H05 with
a different signal (e.g. funding-rate basis carry) that constitutes a
*new* hypothesis row in `HYPOTHESES.md`.

## 5 Conclusion

H05 is rejected; the pipeline that rejected it is the value of this work.
The risk gate, the regime detector, the Purged K-Fold + bootstrap +
deflation triple, the deterministic run-recorder, and the four on-chain
primitives (vault + registry + risk oracle + emergency pause) compose into
a framework where the next five hypotheses can be tested under the same
discipline. Building a trading agent without that discipline produces
plausible-looking equity curves; with it, you produce trustworthy
verdicts.

The breadth side of the problem (IC times sqrt(breadth) in [@grinold2000active])
fundamental law — is unaddressed here. A natural next step is to test
the same sleeve on a basket of 8-12 majors, allowing the signal to win
on diversification rather than per-asset edge. That is a separate
hypothesis (a candidate H06 line under the existing H06 funding-basis
carry).

## References

::: {#refs}
:::
