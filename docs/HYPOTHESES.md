# Pre-registered Research Hypotheses

The framework supports multi-hypothesis testing under DSR / PBO. Hypotheses
*should* be registered in this document **before** running them so the trial
count is fixed and the deflation penalty is honest.

This file is the registry. Add a row before running the corresponding
backtest. Move it to "completed" with verdict (`accepted`, `rejected`,
`inconclusive`) once the run is in.

## Active

| ID  | Title                                  | Statement |
|-----|----------------------------------------|-----------|
| H01 | Time-series momentum, daily, top-4     | A 60-day momentum signal sized by inverse 30-day vol, applied to the four crypto majors, generates a deflated Sharpe > 0.5 over 2024 after 5bps fees and a linear-impact slippage model. |
| H03 | HMM-conditional vol-target              | A vol-target sleeve activated only when the HMM-decoded regime is `RANGING` outperforms an unconditional vol-target sleeve on Sharpe and Calmar. |
| H04 | Drawdown circuit-breaker is non-negative | Under realistic transaction costs, hard-stopping the strategy at a 25% peak-to-trough drawdown does not reduce annualized return by more than 100 bps over a representative bull/bear cycle. |
| H06 | Funding-basis carry on Hyperliquid     | Long-spot / short-perp delta-neutral capture on BTC produces a positive Sharpe after funding payments and 10 bps/side fees in regimes where annualized funding > 8%. |

## Completed

### H02 · BTC/ETH stat-arb log-spread — **rejected (does not survive deflation)**

| field | value |
|---|---|
| dataset | BTC/USDT + ETH/USDT daily, 2024-01-01 → 2024-12-31 (366 bars from Binance via ccxt) |
| sleeve | log-spread = log(BTC) − β · log(ETH); rolling 60-day OLS β; entry at \|z\| > 2.0, exit at \|z\| < 0.5; equal-weight 0.5/leg |
| costs | 10 bps/side on every change in absolute leg weight |
| Sharpe (net, 10 bps) | **-0.1087** |
| Sharpe 95% CI (block bootstrap, block=10, 5k iter) | **[-1.9017, +1.5940]** |
| Probabilistic Sharpe (vs SR=0) | **0.4569** |
| Deflated Sharpe (N=6 trials) | **0.0000** |
| Mean OOS Sharpe (PurgedKFold k=5, embargo=1%) | **-0.1485** |
| Final equity | 0.9780 |
| Days in spread | 157 / 366 |

**Interpretation.** Distinct verdict shape from H05. The point estimate is
near-flat (PSR 0.46 — a coin flip on whether SR > 0); the 95% CI crosses
zero in both directions; OOS folds are split (2 positive, 3 negative). At
N=6 trials the DSR penalty wipes out the borderline PSR. This is *not*
a confidently-negative strategy — it is a *coin-flip* strategy. A naive
reader of the gross Sharpe (0.0153) would call it "promising"; the
deflation discipline correctly classifies it as *not actionable*.

The contrast with H05's strong rejection (Sharpe −2.42, CI entirely
below zero) is itself informative: it shows the framework producing
different verdict signatures rather than mechanically rejecting
everything.

Run artifacts:

* Notebook: [`research/H02_btc_eth_stat_arb.ipynb`](../research/H02_btc_eth_stat_arb.ipynb)
* Tearsheet: [`docs/tearsheets/H02.html`](./tearsheets/H02.html)

---

### H05 · HMM Volatility Regime — **rejected (does not survive deflation)**

| field | value |
|---|---|
| dataset | BTCUSDT 1h, 2024-05-10 → 2026-04-30 (17,281 bars from Binance via ccxt) |
| sleeve | sign(`mom_z_168h`) · clip(`abs(mom_z)`/2, 0, 1); high-vol regime scaled ×0.25 |
| HMM | 2-state Gaussian on (log-return, 24h realized vol); states ranked by vol |
| costs | 10 bps/side on every change in size |
| Sharpe (net, 10 bps) | **-2.4238** |
| Sharpe 95% CI (block bootstrap, block=24, 10k iter) | **[-3.8276, -1.0111]** |
| Probabilistic Sharpe (vs SR=0) | **0.0004** |
| Deflated Sharpe (N=6 trials) | **0.0000** |
| Mean OOS Sharpe (PurgedKFold k=5, embargo=1%) | **-2.4454** |
| **CPCV path-Sharpe** (15 paths · n_groups=6 · n_test=2) | **mean -2.4370 · std 0.5934 · min -3.5673 · max -1.5892 · frac>0: 0.000** |
| Final equity (1.0 = breakeven) | 0.4909 |

**Interpretation.** A 168h-momentum z-score sleeve on BTCUSDT 1h is *anti-correlated*
with forward returns over this window — i.e. the signal would have been a
weak contrarian indicator at best. Adding regime-conditional de-risking did
not rescue it; the high-vol regime contains the bulk of the bleed, so even
a 4× position cut still carries large negative attribution. Once 10 bps/side
fees are charged on the resulting turnover, gross Sharpe -0.41 collapses to
net Sharpe -2.42.

**What this rules out.** The headline alpha for this exact sleeve specification
on this exact venue/window does not exist. It does *not* rule out (a) a
contrarian flip of the signal, (b) longer lookbacks, (c) different cost
models on a venue with maker rebates, (d) different regimes / regime feature
sets, (e) different assets. Each of those would constitute a *new* hypothesis
under DSR's trial-count discipline and would need its own pre-registration
row above before being run.

Run artifacts:

* Notebook: [`research/H05_hmm_volatility_regime.ipynb`](../research/H05_hmm_volatility_regime.ipynb)
* Tearsheet (no inputs): [`docs/tearsheets/H05.html`](./tearsheets/H05.html)
* Cached data: `agent/.praxis_cache/binance/BTC_USDT_1h_2024-05-10_2026-04-30.parquet`

## How to register

1. Pick a unique `H##` ID.
2. Write a single-sentence falsifiable statement that includes the dataset,
   the metric, and the threshold.
3. Open a PR adding a row to "Active" before pressing run.
4. After the run, record the verdict and link to `runs/<timestamp>_<hash>/`
   in "Completed".

## Why pre-registration matters

Every run after the first is a multiple-testing scenario. The Deflated Sharpe
correction in `praxis.backtest.stats.deflated_sharpe` requires a faithful
trial count to penalise selection bias. Tweaking parameters and replaying
without registering doubles the trials honestly required by DSR. Treat the
list above as the cap on what may be reported.
