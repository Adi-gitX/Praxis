from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd


@dataclass
class Metrics:
    total_return: float
    annualized_return: float
    annualized_vol: float
    sharpe: float
    sortino: float
    max_drawdown: float
    calmar: float
    hit_rate: float
    avg_win: float
    avg_loss: float
    win_loss_ratio: float
    n_periods: int
    n_wins: int
    n_losses: int

    def as_dict(self) -> dict[str, float]:
        return {k: float(v) if isinstance(v, (int, float, np.floating)) else v for k, v in self.__dict__.items()}


def compute_metrics(equity: pd.Series, periods_per_year: int = 365) -> Metrics:
    """Performance summary computed from a daily equity curve.

    `periods_per_year=365` is the crypto convention (no trading-day adjustment).
    All ratios assume a zero risk-free rate.
    """
    if len(equity) < 2:
        empty = float("nan")
        return Metrics(empty, empty, empty, empty, empty, empty, empty, empty, empty, empty, empty, 0, 0, 0)

    returns = equity.pct_change().dropna()
    total_return = float(equity.iloc[-1] / equity.iloc[0] - 1.0)
    n_periods = len(returns)
    annualized_return = float((1.0 + returns.mean()) ** periods_per_year - 1.0)
    annualized_vol = float(returns.std(ddof=0) * np.sqrt(periods_per_year))

    sharpe = float(annualized_return / annualized_vol) if annualized_vol > 0 else 0.0

    downside = returns[returns < 0]
    downside_vol = float(downside.std(ddof=0) * np.sqrt(periods_per_year)) if len(downside) > 0 else 0.0
    sortino = float(annualized_return / downside_vol) if downside_vol > 0 else 0.0

    cum = (1.0 + returns).cumprod()
    running_peak = cum.cummax()
    drawdown = (cum / running_peak - 1.0).min()
    max_drawdown = float(abs(drawdown))
    calmar = float(annualized_return / max_drawdown) if max_drawdown > 0 else 0.0

    wins = returns[returns > 0]
    losses = returns[returns < 0]
    hit_rate = float(len(wins) / n_periods) if n_periods > 0 else 0.0
    avg_win = float(wins.mean()) if len(wins) > 0 else 0.0
    avg_loss = float(losses.mean()) if len(losses) > 0 else 0.0
    win_loss_ratio = float(abs(avg_win / avg_loss)) if avg_loss < 0 else 0.0

    return Metrics(
        total_return=total_return,
        annualized_return=annualized_return,
        annualized_vol=annualized_vol,
        sharpe=sharpe,
        sortino=sortino,
        max_drawdown=max_drawdown,
        calmar=calmar,
        hit_rate=hit_rate,
        avg_win=avg_win,
        avg_loss=avg_loss,
        win_loss_ratio=win_loss_ratio,
        n_periods=n_periods,
        n_wins=int(len(wins)),
        n_losses=int(len(losses)),
    )


def walk_forward(
    prices: pd.DataFrame,
    runner: Callable[[pd.DataFrame], pd.Series],
    train_window: int = 180,
    test_window: int = 60,
    step: int | None = None,
) -> pd.DataFrame:
    """Walk-forward analysis: roll a (train, test) window across the data and
    evaluate `runner` on each test fold. `runner` receives the slice for that
    fold's *test* window and returns the equity curve over that window.

    Returns a DataFrame with one row per fold (train_start, train_end, test_start,
    test_end, sharpe, max_drawdown, total_return).
    """
    if step is None:
        step = test_window

    rows = []
    n = len(prices)
    start = 0
    while start + train_window + test_window <= n:
        train = prices.iloc[start : start + train_window]
        test = prices.iloc[start + train_window : start + train_window + test_window]
        equity = runner(test)
        m = compute_metrics(equity)
        rows.append(
            {
                "train_start": train.index[0],
                "train_end": train.index[-1],
                "test_start": test.index[0],
                "test_end": test.index[-1],
                "sharpe": m.sharpe,
                "sortino": m.sortino,
                "max_drawdown": m.max_drawdown,
                "total_return": m.total_return,
            }
        )
        start += step
    return pd.DataFrame(rows)
