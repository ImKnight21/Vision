"""Volatility estimators.

Close-to-close is the familiar one, but it throws away the intrabar range.
The range-based estimators (Parkinson, Garman-Klass, Rogers-Satchell) use the
high and low too, so they converge on the true volatility with far fewer bars —
useful when a coin only has a short history. All results are annualised.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.analytics.returns import log_returns, periods_per_year

_LN2 = float(np.log(2.0))


def _tail(frame: pd.DataFrame | pd.Series, window: int | None):
    return frame if window is None else frame.tail(window)


def _annualise(per_period_variance: float, interval: str) -> float:
    return float(np.sqrt(max(per_period_variance, 0.0) * periods_per_year(interval)))


def close_to_close(
    close: pd.Series, interval: str, window: int | None = None
) -> float | None:
    """Standard deviation of log returns, annualised. The textbook estimator."""
    returns = _tail(log_returns(close), window)
    if len(returns) < 2:
        return None
    # ddof=1: we are estimating from a sample, not describing a population.
    return _annualise(float(returns.var(ddof=1)), interval)


def ewma(
    close: pd.Series, interval: str, lam: float = 0.94, window: int | None = None
) -> float | None:
    """RiskMetrics EWMA volatility: recent bars dominate, old ones decay away.

    `lam` is the decay factor; 0.94 is the RiskMetrics daily convention.
    """
    returns = _tail(log_returns(close), window)
    if len(returns) < 2:
        return None
    if not 0.0 < lam < 1.0:
        raise ValueError("lam must lie strictly between 0 and 1")
    # Newest bar gets weight (1-lam), each older bar lam times the next.
    values = returns.to_numpy(dtype=float)[::-1]
    weights = (1.0 - lam) * lam ** np.arange(len(values))
    weights /= weights.sum()
    variance = float(np.sum(weights * values**2))
    return _annualise(variance, interval)


def parkinson(
    frame: pd.DataFrame, interval: str, window: int | None = None
) -> float | None:
    """High-low estimator. Roughly 5x more efficient than close-to-close,
    but it assumes no drift and ignores overnight gaps."""
    frame = _tail(frame, window)
    high, low = frame["high"], frame["low"]
    mask = (high > 0) & (low > 0)
    if mask.sum() < 2:
        return None
    hl = np.log(high[mask] / low[mask]) ** 2
    return _annualise(float(hl.mean()) / (4.0 * _LN2), interval)


def garman_klass(
    frame: pd.DataFrame, interval: str, window: int | None = None
) -> float | None:
    """Uses the full OHLC bar. The most efficient of the three when the
    open-to-close move is informative, but it too assumes zero drift."""
    frame = _tail(frame, window)
    o, h, l, c = frame["open"], frame["high"], frame["low"], frame["close"]
    mask = (o > 0) & (h > 0) & (l > 0) & (c > 0)
    if mask.sum() < 2:
        return None
    hl = np.log(h[mask] / l[mask]) ** 2
    co = np.log(c[mask] / o[mask]) ** 2
    variance = float((0.5 * hl - (2.0 * _LN2 - 1.0) * co).mean())
    return _annualise(variance, interval)


def rogers_satchell(
    frame: pd.DataFrame, interval: str, window: int | None = None
) -> float | None:
    """Range estimator that stays unbiased when the price is trending —
    the one to trust when a coin is in a sustained run."""
    frame = _tail(frame, window)
    o, h, l, c = frame["open"], frame["high"], frame["low"], frame["close"]
    mask = (o > 0) & (h > 0) & (l > 0) & (c > 0)
    if mask.sum() < 2:
        return None
    o, h, l, c = o[mask], h[mask], l[mask], c[mask]
    term = np.log(h / c) * np.log(h / o) + np.log(l / c) * np.log(l / o)
    return _annualise(float(term.mean()), interval)


def rolling_close_to_close(
    close: pd.Series, interval: str, window: int
) -> pd.Series:
    """Annualised close-to-close volatility as a series, for plotting."""
    returns = log_returns(close)
    if len(returns) < window:
        return pd.Series(dtype=float)
    scale = float(np.sqrt(periods_per_year(interval)))
    return (returns.rolling(window).std(ddof=1) * scale).dropna()
