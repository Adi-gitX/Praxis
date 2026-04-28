"""Gaussian HMM regime detector.

References:
    Hamilton, J. D. (1989). A New Approach to the Economic Analysis of
        Nonstationary Time Series and the Business Cycle. Econometrica.
    Bilmes, J. A. (1998). A gentle tutorial of the EM algorithm and its
        application to parameter estimation for Gaussian mixture and hidden
        Markov models.

Fits a 2- or 3-state Gaussian HMM on the joint distribution of
(log-return, realized-vol). Viterbi-decoded regime series is then exposed
as a `pandas.Series` aligned to the input index. State labels are assigned
post-hoc by ranking states on realized vol so that the lowest-vol state is
always state 0 — this gives stable regime semantics across re-fits.

Implementation: pure-numpy EM. We deliberately avoid `hmmlearn` here to keep
the dependency surface small; for production use the same module can be
swapped to `hmmlearn.GaussianHMM` with no caller changes.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from praxis._typed_np import log_df
from praxis.types import Regime

_REGIME_BY_RANK = {
    2: [Regime.RANGING, Regime.HIGH_VOL],
    3: [Regime.RANGING, Regime.TRENDING, Regime.CRISIS],
    4: [Regime.RANGING, Regime.TRENDING, Regime.HIGH_VOL, Regime.CRISIS],
}


@dataclass
class HMMRegimeDetector:
    n_states: int = 3
    realized_vol_window: int = 14
    max_iter: int = 100
    tol: float = 1e-4
    seed: int = 42

    def __post_init__(self) -> None:
        if self.n_states not in _REGIME_BY_RANK:
            raise ValueError(f"n_states must be in {sorted(_REGIME_BY_RANK)}")

    def fit_predict(self, prices: pd.DataFrame) -> pd.Series:
        log_returns = log_df(prices).diff().mean(axis=1).dropna()
        vol = log_returns.rolling(self.realized_vol_window).std(ddof=0).dropna()
        idx = vol.index.intersection(log_returns.index)
        features = np.column_stack(
            [log_returns.loc[idx].to_numpy(), vol.loc[idx].to_numpy()]
        )
        states, vol_means = self._em(features)
        ranking = np.argsort(vol_means)
        rank_map = {int(s): r for r, s in enumerate(ranking)}
        labels = _REGIME_BY_RANK[self.n_states]
        regime = pd.Series(
            [labels[rank_map[int(s)]].value for s in states],
            index=idx,
            name="regime",
        )
        return regime

    def _em(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        rng = np.random.default_rng(self.seed)
        n, d = X.shape
        k = self.n_states
        # Init: random assignment, then compute moments.
        z = rng.integers(0, k, size=n)
        means = np.array([X[z == s].mean(axis=0) if (z == s).any() else X.mean(axis=0) for s in range(k)])
        covs = np.array([np.cov(X[z == s].T) + 1e-6 * np.eye(d) if (z == s).sum() > d else np.cov(X.T) + 1e-6 * np.eye(d) for s in range(k)])
        pi = np.full(k, 1.0 / k)
        A = np.full((k, k), 1.0 / k)
        prev_ll = -np.inf

        for _ in range(self.max_iter):
            log_b = self._log_emission(X, means, covs)
            log_alpha = self._forward(np.log(pi + 1e-12), np.log(A + 1e-12), log_b)
            log_beta = self._backward(np.log(A + 1e-12), log_b)
            log_gamma = log_alpha + log_beta
            log_gamma -= _logsumexp(log_gamma, axis=1, keepdims=True)
            gamma = np.exp(log_gamma)

            log_xi = (
                log_alpha[:-1, :, None]
                + np.log(A + 1e-12)[None, :, :]
                + log_b[1:, None, :]
                + log_beta[1:, None, :]
            )
            log_xi -= _logsumexp(log_xi.reshape(n - 1, -1), axis=1, keepdims=True)[:, :, None]
            xi = np.exp(log_xi)

            pi = gamma[0] / gamma[0].sum()
            A = xi.sum(axis=0)
            A /= A.sum(axis=1, keepdims=True)

            for s in range(k):
                w = gamma[:, s][:, None]
                total = w.sum() + 1e-12
                means[s] = (w * X).sum(axis=0) / total
                centered = X - means[s]
                covs[s] = (w * centered).T @ centered / total + 1e-6 * np.eye(d)

            ll = float(_logsumexp(log_alpha[-1], axis=0))
            if abs(ll - prev_ll) < self.tol:
                break
            prev_ll = ll

        states = self._viterbi(np.log(pi + 1e-12), np.log(A + 1e-12), log_b)
        vol_means = means[:, 1]
        return states, vol_means

    @staticmethod
    def _log_emission(X: np.ndarray, means: np.ndarray, covs: np.ndarray) -> np.ndarray:
        n, d = X.shape
        k = means.shape[0]
        out = np.empty((n, k))
        for s in range(k):
            cov = covs[s]
            sign, logdet = np.linalg.slogdet(cov)
            if sign <= 0:
                out[:, s] = -np.inf
                continue
            inv = np.linalg.inv(cov)
            diff = X - means[s]
            quad = np.einsum("ij,jk,ik->i", diff, inv, diff)
            out[:, s] = -0.5 * (d * np.log(2 * np.pi) + logdet + quad)
        return out

    @staticmethod
    def _forward(log_pi: np.ndarray, log_A: np.ndarray, log_b: np.ndarray) -> np.ndarray:
        n, k = log_b.shape
        log_alpha = np.empty_like(log_b)
        log_alpha[0] = log_pi + log_b[0]
        for t in range(1, n):
            log_alpha[t] = log_b[t] + _logsumexp(log_alpha[t - 1][:, None] + log_A, axis=0)
        return log_alpha

    @staticmethod
    def _backward(log_A: np.ndarray, log_b: np.ndarray) -> np.ndarray:
        n, k = log_b.shape
        log_beta = np.zeros_like(log_b)
        for t in range(n - 2, -1, -1):
            log_beta[t] = _logsumexp(log_A + log_b[t + 1] + log_beta[t + 1], axis=1)
        return log_beta

    @staticmethod
    def _viterbi(log_pi: np.ndarray, log_A: np.ndarray, log_b: np.ndarray) -> np.ndarray:
        n, k = log_b.shape
        delta = np.empty_like(log_b)
        psi = np.zeros((n, k), dtype=int)
        delta[0] = log_pi + log_b[0]
        for t in range(1, n):
            scores = delta[t - 1][:, None] + log_A
            psi[t] = np.argmax(scores, axis=0)
            delta[t] = log_b[t] + np.max(scores, axis=0)
        path = np.empty(n, dtype=int)
        path[-1] = int(np.argmax(delta[-1]))
        for t in range(n - 2, -1, -1):
            path[t] = psi[t + 1, path[t + 1]]
        return path


def _logsumexp(a: np.ndarray, axis: int | None = None, keepdims: bool = False) -> np.ndarray:
    a_max = np.max(a, axis=axis, keepdims=True)
    if not np.isfinite(a_max).all():
        a_max = np.where(np.isfinite(a_max), a_max, 0.0)
    out = np.log(np.sum(np.exp(a - a_max), axis=axis, keepdims=True)) + a_max
    if not keepdims:
        if axis is None:
            return np.asarray(out).reshape(())
        return np.asarray(np.squeeze(out, axis=axis))
    return np.asarray(out)
