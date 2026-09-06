"""Market-regime measures: does this asset trend, or does it revert?

Volatility tells you how far price moves. These tell you whether those moves
tend to continue or to be given back, which is the part that decides whether a
breakout or a fade is the sensible read.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.analytics.returns import log_returns
from app.analytics.volatility import rolling_close_to_close


def hurst_exponent(close: pd.Series, min_window: int = 8) -> float | None:
    """Rescaled-range (R/S) estimate of the Hurst exponent.

    Reads as: 0.5 is a random walk, above 0.5 means moves persist (trending),
    below 0.5 means they get given back (mean-reverting). Crypto majors usually
    land slightly above 0.5 on daily bars.

    Needs a few hundred bars to be worth anything; returns None below that.
    """
    returns = log_returns(close).to_numpy(dtype=float)
    n = len(returns)
    if n < 128:
        return None

    max_window = n // 2
    if max_window <= min_window:
        return None

    # Log-spaced window sizes: the fit is a slope in log-log space, so the
    # samples should be evenly spread there rather than linearly.
    windows = np.unique(
        np.logspace(np.log10(min_window), np.log10(max_window), 20).astype(int)
    )

    sizes: list[float] = []
    ratios: list[float] = []
    for window in windows:
        chunks = n // window
        if chunks < 1:
            continue
        values = []
        for index in range(chunks):
            segment = returns[index * window : (index + 1) * window]
            deviations = np.cumsum(segment - segment.mean())
            spread = float(deviations.max() - deviations.min())
            scale = float(segment.std(ddof=1))
            if scale > 0:
                values.append(spread / scale)
        if values:
            sizes.append(float(window))
            ratios.append(float(np.mean(values)))

    if len(sizes) < 4:
        return None

    slope, _ = np.polyfit(np.log(sizes), np.log(ratios), 1)
    return float(slope)


def autocorrelation(close: pd.Series, lag: int = 1) -> float | None:
    """Correlation of each return with the one `lag` bars earlier.

    Positive means momentum: up bars tend to follow up bars. Negative means
    reversal. The magnitude is usually small; the sign is the signal.
    """
    returns = log_returns(close)
    if len(returns) < lag + 30:
        return None
    # A series that never moves has no variance to correlate, and pandas would
    # divide by zero to tell us so.
    if float(returns.std(ddof=1)) == 0.0:
        return None
    value = returns.autocorr(lag)
    return None if pd.isna(value) else float(value)


def volatility_of_volatility(
    close: pd.Series, interval: str, window: int = 30
) -> float | None:
    """How unstable the volatility itself is, as a coefficient of variation.

    A high number means the asset switches between calm and violent regimes
    rather than staying at one level, so any single volatility figure has a
    short shelf life.
    """
    series = rolling_close_to_close(close, interval, window)
    if len(series) < window:
        return None
    mean = float(series.mean())
    if mean <= 0:
        return None
    return float(series.std(ddof=1) / mean)


def volatility_percentile(
    close: pd.Series, interval: str, window: int = 30
) -> float | None:
    """Where current volatility sits in this asset's own history, 0..1.

    This is the context an absolute figure lacks. 60% annualised means nothing
    on its own; 60% at the 95th percentile of its own past says the asset is
    about as agitated as it ever gets.
    """
    series = rolling_close_to_close(close, interval, window)
    if len(series) < window * 2:
        return None
    current = float(series.iloc[-1])
    return float((series <= current).mean())


def trend_strength(close: pd.Series, window: int = 50) -> float | None:
    """R-squared of a straight line fit through log price, 0..1.

    Answers "how orderly is this move?" rather than "which way?". A high value
    means a clean directional run; a low one means chop that happens to have
    drifted. Pair it with the sign of the slope.
    """
    series = close.dropna().tail(window)
    if len(series) < max(10, window // 2):
        return None
    values = np.log(series.to_numpy(dtype=float))
    if not np.all(np.isfinite(values)):
        return None
    x = np.arange(len(values), dtype=float)
    slope, intercept = np.polyfit(x, values, 1)
    fitted = slope * x + intercept
    total = float(((values - values.mean()) ** 2).sum())
    if total == 0:
        return None
    residual = float(((values - fitted) ** 2).sum())
    return float(1.0 - residual / total)


def trend_change(close: pd.Series, window: int = 50) -> float | None:
    """Change along the fitted trend line across the window, as a fraction.

    Deliberately *not* annualised. Compounding a 50-bar drift out to a year
    produces figures like +1300% that are arithmetically correct and
    analytically worthless; the honest statement is how far the fitted line
    travelled over the window it was fitted to.

    Read it beside `trend_strength`: a large change with a low R-squared is
    noise that happened to drift.
    """
    series = close.dropna().tail(window)
    if len(series) < max(10, window // 2):
        return None
    values = np.log(series.to_numpy(dtype=float))
    if not np.all(np.isfinite(values)):
        return None
    x = np.arange(len(values), dtype=float)
    slope, _ = np.polyfit(x, values, 1)
    return float(np.expm1(slope * (len(values) - 1)))
