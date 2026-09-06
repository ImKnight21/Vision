"""Drawdown, risk-adjusted return, and tail-risk measures."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from app.analytics.returns import log_returns, periods_per_year, simple_returns


@dataclass(frozen=True)
class Drawdown:
    """A peak-to-trough decline, as a negative fraction (-0.35 == -35%)."""

    max_drawdown: float | None
    peak_at: pd.Timestamp | None
    trough_at: pd.Timestamp | None
    recovered_at: pd.Timestamp | None
    current_drawdown: float | None


def drawdown_series(close: pd.Series) -> pd.Series:
    """Fractional distance below the running high, at every point in time."""
    close = close.dropna()
    if close.empty:
        return pd.Series(dtype=float)
    running_peak = close.cummax()
    return close / running_peak - 1.0


def analyse_drawdown(close: pd.Series) -> Drawdown:
    close = close.dropna()
    if len(close) < 2:
        return Drawdown(None, None, None, None, None)

    series = drawdown_series(close)
    trough_at = series.idxmin()
    max_dd = float(series.loc[trough_at])

    # The peak is the last time we were at a running high before the trough.
    before_trough = close.loc[:trough_at]
    peak_at = before_trough.idxmax()
    peak_value = float(before_trough.max())

    # Recovery is the first bar after the trough to close back at the old peak.
    after_trough = close.loc[trough_at:]
    regained = after_trough[after_trough >= peak_value]
    recovered_at = regained.index[0] if len(regained) else None

    return Drawdown(
        max_drawdown=max_dd,
        peak_at=peak_at,
        trough_at=trough_at,
        recovered_at=recovered_at,
        current_drawdown=float(series.iloc[-1]),
    )


def sharpe_ratio(
    close: pd.Series, interval: str, risk_free_rate: float = 0.0
) -> float | None:
    """Excess return per unit of total volatility, annualised.

    `risk_free_rate` is an annual rate; 0 is the usual convention for crypto.
    """
    returns = log_returns(close)
    if len(returns) < 2:
        return None
    ppy = periods_per_year(interval)
    std = float(returns.std(ddof=1))
    if std == 0.0:
        return None
    excess = float(returns.mean()) - risk_free_rate / ppy
    return float(excess / std * np.sqrt(ppy))


def sortino_ratio(
    close: pd.Series, interval: str, risk_free_rate: float = 0.0
) -> float | None:
    """Like Sharpe, but only downside moves count as risk.

    Upside volatility is what you want, so penalising it — as Sharpe does —
    understates a strategy that jumps rather than bleeds.
    """
    returns = log_returns(close)
    if len(returns) < 2:
        return None
    ppy = periods_per_year(interval)
    target = risk_free_rate / ppy
    downside = returns[returns < target] - target
    if downside.empty:
        return None
    # Deviations are measured against the target over the *full* sample, not
    # just the losing bars, which is what distinguishes this from a plain std.
    downside_dev = float(np.sqrt((downside**2).sum() / len(returns)))
    if downside_dev == 0.0:
        return None
    excess = float(returns.mean()) - target
    return float(excess / downside_dev * np.sqrt(ppy))


def calmar_ratio(close: pd.Series, interval: str) -> float | None:
    """Annualised return divided by the depth of the worst drawdown."""
    from app.analytics.returns import cagr

    growth = cagr(close, interval)
    max_dd = analyse_drawdown(close).max_drawdown
    if growth is None or max_dd is None or max_dd == 0.0:
        return None
    return float(growth / abs(max_dd))


def value_at_risk(
    close: pd.Series, confidence: float = 0.95, horizon: int = 1
) -> float | None:
    """Historical VaR: the loss the worst `1-confidence` of bars exceed.

    Returned as a negative fraction. Historical rather than parametric, because
    crypto returns are far too fat-tailed for a normal assumption to hold.
    """
    returns = simple_returns(close)
    if len(returns) < 20:
        return None
    quantile = float(np.quantile(returns.to_numpy(dtype=float), 1.0 - confidence))
    return float(quantile * np.sqrt(max(horizon, 1)))


def conditional_value_at_risk(
    close: pd.Series, confidence: float = 0.95
) -> float | None:
    """Expected shortfall: the average loss *given* that VaR was breached.

    This is the number that says how bad the bad days actually get.
    """
    returns = simple_returns(close)
    if len(returns) < 20:
        return None
    values = returns.to_numpy(dtype=float)
    threshold = float(np.quantile(values, 1.0 - confidence))
    tail = values[values <= threshold]
    if tail.size == 0:
        return None
    return float(tail.mean())


def return_distribution(close: pd.Series) -> dict[str, float | None]:
    """Shape of the return distribution: asymmetry and tail weight."""
    returns = simple_returns(close)
    if len(returns) < 4:
        return {"skew": None, "kurtosis": None, "best": None, "worst": None,
                "positive_share": None}
    return {
        # Negative skew means the big moves tend to be downward.
        "skew": float(returns.skew()),
        # Excess kurtosis; 0 is normal, higher means fatter tails.
        "kurtosis": float(returns.kurtosis()),
        "best": float(returns.max()),
        "worst": float(returns.min()),
        "positive_share": float((returns > 0).mean()),
    }


def ulcer_index(close: pd.Series) -> float | None:
    """Root-mean-square drawdown: depth and duration in one number.

    Max drawdown reports the single worst moment. The Ulcer Index asks how deep
    the water was on average across the whole window, so a long shallow slump
    and a brief violent crash stop looking alike. Returned as a positive
    fraction; lower is calmer.
    """
    series = drawdown_series(close)
    if len(series) < 2:
        return None
    return float(np.sqrt((series**2).mean()))


def time_under_water(close: pd.Series) -> dict[str, float | int | None]:
    """How much of the window was spent below a previous high, and for how long.

    `share` is the fraction of bars in drawdown; `longest_bars` is the longest
    unbroken stretch. An asset can post a fine annual return and still have been
    underwater for nine tenths of the year, which is the part that decides
    whether a position was actually holdable.
    """
    series = drawdown_series(close)
    if len(series) < 2:
        return {"share": None, "longest_bars": None, "current_bars": None}

    underwater = (series < 0).to_numpy()

    longest = current = 0
    for flag in underwater:
        current = current + 1 if flag else 0
        longest = max(longest, current)

    return {
        "share": float(underwater.mean()),
        "longest_bars": int(longest),
        # `current` ends the loop holding the trailing run, which is the streak
        # the asset is in right now.
        "current_bars": int(current),
    }


def recovery_factor(close: pd.Series) -> float | None:
    """Total return divided by the depth of the worst drawdown.

    How much the asset earned per unit of its own worst decline. Unlike Calmar
    it uses the raw window return rather than an annualised one, so it is not
    distorted by a short sample.
    """
    from app.analytics.returns import total_return

    profit = total_return(close)
    max_dd = analyse_drawdown(close).max_drawdown
    if profit is None or max_dd is None or max_dd == 0.0:
        return None
    return float(profit / abs(max_dd))


def tail_ratio(close: pd.Series, quantile: float = 0.95) -> float | None:
    """Size of the best tail against the worst: |95th pct| / |5th pct|.

    Above 1 means the good outliers were bigger than the bad ones. This is the
    asymmetry that skew hints at, stated in units you can act on.
    """
    returns = simple_returns(close)
    if len(returns) < 30:
        return None
    values = returns.to_numpy(dtype=float)
    upside = float(np.quantile(values, quantile))
    downside = abs(float(np.quantile(values, 1.0 - quantile)))
    if downside == 0:
        return None
    return float(upside / downside)


def omega_ratio(close: pd.Series, threshold: float = 0.0) -> float | None:
    """Total gains above `threshold` divided by total losses below it.

    Uses the whole distribution rather than its first two moments, so unlike
    Sharpe it does not quietly assume the returns are normal - which for crypto
    they emphatically are not.
    """
    returns = simple_returns(close)
    if len(returns) < 30:
        return None
    excess = returns.to_numpy(dtype=float) - threshold
    gains = float(excess[excess > 0].sum())
    losses = float(-excess[excess < 0].sum())
    if losses == 0:
        return None
    return float(gains / losses)


def gain_to_pain(close: pd.Series) -> float | None:
    """Sum of all returns divided by the sum of the losing ones.

    A blunt but honest read on whether the winners paid for the losers.
    """
    returns = simple_returns(close)
    if len(returns) < 30:
        return None
    values = returns.to_numpy(dtype=float)
    pain = float(-values[values < 0].sum())
    if pain == 0:
        return None
    return float(values.sum() / pain)
