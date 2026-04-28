"""Advanced performance statistics.

References:
    Bailey, D. & López de Prado, M. (2012). The Sharpe Ratio Efficient Frontier.
        Journal of Risk, 15(2). [PSR derivation.]
    Bailey, D. & López de Prado, M. (2014). The Deflated Sharpe Ratio:
        Correcting for Selection Bias, Backtest Overfitting and Non-Normality.
        Journal of Portfolio Management, 40(5). [DSR derivation.]
    Bailey, D., Borwein, J., López de Prado, M. & Zhu, Q. (2017). The
        Probability of Backtest Overfitting. Journal of Computational Finance.

The classical Sharpe ratio is a noisy point estimate. With finite N, non-normal
returns, and a search over many trials, it is biased upward. PSR/DSR explicitly
correct for these.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd

PERIODS_PER_YEAR_CRYPTO = 365


def _safe_returns(returns: np.ndarray | pd.Series) -> np.ndarray:
    arr = np.asarray(returns, dtype=float).ravel()
    finite_mask = np.isfinite(arr)
    return np.asarray(arr[finite_mask], dtype=float)


_STD_EPS = 1e-12


def sharpe(returns: np.ndarray | pd.Series, periods_per_year: int = PERIODS_PER_YEAR_CRYPTO) -> float:
    arr = _safe_returns(returns)
    if arr.size < 2:
        return 0.0
    std = float(arr.std(ddof=0))
    if std < _STD_EPS:
        return 0.0
    return float(arr.mean() / std * math.sqrt(periods_per_year))


def sortino(returns: np.ndarray | pd.Series, periods_per_year: int = PERIODS_PER_YEAR_CRYPTO) -> float:
    arr = _safe_returns(returns)
    if arr.size < 2:
        return 0.0
    downside = arr[arr < 0]
    if downside.size == 0:
        return 0.0
    dstd = float(downside.std(ddof=0))
    if dstd < _STD_EPS:
        return 0.0
    return float(arr.mean() / dstd * math.sqrt(periods_per_year))


def max_drawdown(equity: np.ndarray | pd.Series) -> float:
    arr = np.asarray(equity, dtype=float).ravel()
    if arr.size < 2:
        return 0.0
    peak = np.maximum.accumulate(arr)
    drawdown = (arr - peak) / peak
    return float(abs(drawdown.min()))


def calmar(returns: np.ndarray | pd.Series, equity: np.ndarray | pd.Series, periods_per_year: int = PERIODS_PER_YEAR_CRYPTO) -> float:
    arr = _safe_returns(returns)
    mdd = max_drawdown(equity)
    if mdd == 0 or arr.size < 2:
        return 0.0
    annualised = (1.0 + arr.mean()) ** periods_per_year - 1.0
    return float(annualised / mdd)


def probabilistic_sharpe(
    returns: np.ndarray | pd.Series,
    sr_benchmark: float = 0.0,
) -> float:
    """Probabilistic Sharpe Ratio — P(SR > sr_benchmark) under non-normal returns.

    Bailey & López de Prado (2012). The Sharpe Ratio Efficient Frontier.
    """
    arr = _safe_returns(returns)
    n = arr.size
    if n < 5:
        return 0.0
    std = float(arr.std(ddof=0))
    if std < _STD_EPS:
        return 0.0
    sr = arr.mean() / std

    skew = float(((arr - arr.mean()) ** 3).mean() / (std ** 3))
    kurt = float(((arr - arr.mean()) ** 4).mean() / (std ** 4)) - 3.0

    denom_inner = 1.0 - skew * sr + ((kurt - 1.0) / 4.0) * sr * sr
    if denom_inner <= 0:
        return 0.0
    se = math.sqrt(denom_inner / (n - 1))
    if se < _STD_EPS:
        return 0.0
    z = (sr - sr_benchmark) / se
    return float(_normal_cdf(z))


def deflated_sharpe(
    returns: np.ndarray | pd.Series,
    trial_sharpes: np.ndarray | pd.Series | None = None,
    n_trials: int | None = None,
) -> float:
    """Deflated Sharpe Ratio — PSR adjusted for the number of independent trials.

    Bailey & López de Prado (2014). Adjusts the SR* benchmark from zero to the
    expected maximum SR under the null hypothesis of zero edge across `n_trials`
    independent attempts. The deflation grows with both the number of trials
    and the variance of trial Sharpes — i.e. it punishes wide parameter
    searches harder than narrow ones.

    Either pass `trial_sharpes` (an array of SR estimates from your search) or
    `n_trials` and the function will assume unit variance among trials.
    """
    arr = _safe_returns(returns)
    if arr.size < 5:
        return 0.0

    if trial_sharpes is not None:
        ts = np.asarray(trial_sharpes, dtype=float).ravel()
        ts = ts[np.isfinite(ts)]
        if ts.size < 2:
            return probabilistic_sharpe(arr)
        var_trials = ts.var(ddof=1)
        n = ts.size
    elif n_trials is not None and n_trials >= 2:
        var_trials = 1.0
        n = int(n_trials)
    else:
        return probabilistic_sharpe(arr)

    # Expected maximum of N standard-normal draws (Bailey/López de Prado eq.):
    # E[max] ≈ (1 - γ)·Φ⁻¹(1 - 1/N) + γ·Φ⁻¹(1 - 1/(N·e))
    euler_mascheroni = 0.5772156649
    e = math.e
    expected_max = (1.0 - euler_mascheroni) * _normal_ppf(1.0 - 1.0 / n) + \
        euler_mascheroni * _normal_ppf(1.0 - 1.0 / (n * e))
    sr_star = math.sqrt(var_trials) * expected_max
    return probabilistic_sharpe(arr, sr_benchmark=sr_star)


def block_bootstrap_ci(
    returns: np.ndarray | pd.Series,
    stat_fn: Callable[[np.ndarray], float] | None = None,
    n_iter: int = 5_000,
    block_size: int = 20,
    alpha: float = 0.05,
    seed: int = 42,
) -> tuple[float, float, float]:
    """Stationary block-bootstrap confidence interval for an arbitrary statistic.

    `block_size` should be set to roughly the autocorrelation length of the
    returns series. For daily crypto returns 5-30 is a reasonable window.

    Returns: (point_estimate, ci_low, ci_high) at the (1 - alpha) level.
    """
    arr = _safe_returns(returns)
    n = arr.size
    if n < block_size * 2:
        raise ValueError(f"Series too short for block bootstrap (n={n}, block={block_size}).")
    fn = stat_fn or sharpe
    rng = np.random.default_rng(seed)

    point = float(fn(arr))
    samples = np.empty(n_iter, dtype=float)
    for i in range(n_iter):
        sample = _resample_blocks(arr, block_size, n, rng)
        samples[i] = float(fn(sample))
    samples.sort()
    lo = float(samples[int(alpha / 2 * n_iter)])
    hi = float(samples[int((1 - alpha / 2) * n_iter) - 1])
    return point, lo, hi


def probability_of_backtest_overfit(path_sharpes: np.ndarray | pd.DataFrame) -> float:
    """Probability of Backtest Overfit (PBO) from a CPCV path-Sharpe matrix.

    Bailey, Borwein, López de Prado & Zhu (2017). For each split:
        - Rank trials in the in-sample (IS) half.
        - The trial selected by the IS-best is then evaluated on the OOS half.
        - PBO is the fraction of splits in which the IS-best ranks below
          median in OOS.

    Input shape: (n_splits, n_trials) — rows are splits, columns are trial
    Sharpes computed on the OOS half. The IS half is presumed encoded by
    sequential pairs of splits (split_2k = IS, split_2k+1 = OOS) — for our
    purposes here we receive only OOS values and assume an internal IS
    selection upstream.

    Practical convention: pass the matrix from `cpcv_path_sharpes` and the
    function expects each row to contain trial Sharpes evaluated on a single
    held-out path, with column 0 corresponding to the trial that won IS.
    """
    arr = np.asarray(path_sharpes, dtype=float)
    if arr.ndim != 2 or arr.shape[1] < 2:
        raise ValueError("path_sharpes must be 2-D with >= 2 trial columns.")
    n_splits, n_trials = arr.shape
    median_idx = n_trials // 2
    flips = 0
    for row in arr:
        order = np.argsort(-row)  # descending
        rank_of_zero = int(np.where(order == 0)[0][0])
        if rank_of_zero >= median_idx:
            flips += 1
    return float(flips / n_splits)


def _normal_cdf(x: float) -> float:
    # Abramowitz/Stegun 26.2.17 via erf
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _normal_ppf(p: float) -> float:
    """Inverse normal CDF (Beasley-Springer / Moro). Stable enough for this use."""
    if not (0.0 < p < 1.0):
        raise ValueError("p must be in (0, 1).")
    a = [
        -3.969683028665376e+01,  2.209460984245205e+02,
        -2.759285104469687e+02,  1.383577518672690e+02,
        -3.066479806614716e+01,  2.506628277459239e+00,
    ]
    b = [
        -5.447609879822406e+01,  1.615858368580409e+02,
        -1.556989798598866e+02,  6.680131188771972e+01,
        -1.328068155288572e+01,
    ]
    c = [
        -7.784894002430293e-03, -3.223964580411365e-01,
        -2.400758277161838e+00, -2.549732539343734e+00,
        4.374664141464968e+00,  2.938163982698783e+00,
    ]
    d = [
        7.784695709041462e-03,  3.224671290700398e-01,
        2.445134137142996e+00,  3.754408661907416e+00,
    ]
    plow = 0.02425
    phigh = 1 - plow
    if p < plow:
        q = math.sqrt(-2.0 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
    if p <= phigh:
        q = p - 0.5
        r = q * q
        return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
               (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1.0)
    q = math.sqrt(-2.0 * math.log(1.0 - p))
    return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
           ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)


def _resample_blocks(arr: np.ndarray, block_size: int, n: int, rng: np.random.Generator) -> np.ndarray:
    out = np.empty(n, dtype=arr.dtype)
    i = 0
    while i < n:
        start = int(rng.integers(0, arr.size - block_size + 1))
        end = min(i + block_size, n)
        out[i:end] = arr[start : start + (end - i)]
        i = end
    return out


@dataclass
class StatsReport:
    sharpe: float
    sortino: float
    calmar: float
    max_drawdown: float
    psr: float
    dsr: float
    sharpe_ci_low: float
    sharpe_ci_high: float

    def as_dict(self) -> dict[str, float]:
        return self.__dict__.copy()


def full_report(
    returns: np.ndarray | pd.Series,
    equity: np.ndarray | pd.Series,
    n_trials: int = 1,
    bootstrap: bool = True,
) -> StatsReport:
    sr = sharpe(returns)
    so = sortino(returns)
    ca = calmar(returns, equity)
    mdd = max_drawdown(equity)
    psr = probabilistic_sharpe(returns)
    dsr = deflated_sharpe(returns, n_trials=n_trials) if n_trials >= 2 else psr
    if bootstrap and len(_safe_returns(returns)) >= 60:
        _, lo, hi = block_bootstrap_ci(returns, sharpe, n_iter=2_000, block_size=20)
    else:
        lo, hi = float("nan"), float("nan")
    return StatsReport(
        sharpe=sr,
        sortino=so,
        calmar=ca,
        max_drawdown=mdd,
        psr=psr,
        dsr=dsr,
        sharpe_ci_low=lo,
        sharpe_ci_high=hi,
    )
