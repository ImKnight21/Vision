"""Return series and the calendar conventions the rest of the math depends on."""

from __future__ import annotations

import numpy as np
import pandas as pd

# Crypto trades continuously, so a year is 365 calendar days rather than the
# ~252 trading days used for equities. Every annualisation below assumes this.
SECONDS_PER_YEAR = 365 * 24 * 60 * 60

INTERVAL_SECONDS: dict[str, int] = {
    "1m": 60,
    "3m": 3 * 60,
    "5m": 5 * 60,
    "15m": 15 * 60,
    "30m": 30 * 60,
    "1h": 60 * 60,
    "2h": 2 * 60 * 60,
    "4h": 4 * 60 * 60,
    "6h": 6 * 60 * 60,
    "12h": 12 * 60 * 60,
    "1d": 24 * 60 * 60,
    "3d": 3 * 24 * 60 * 60,
    "1w": 7 * 24 * 60 * 60,
}


def periods_per_year(interval: str) -> float:
    """How many bars of `interval` fit in a year. Raises on unknown intervals."""
    try:
        return SECONDS_PER_YEAR / INTERVAL_SECONDS[interval]
    except KeyError:  # pragma: no cover - guarded by the router's validation
        raise ValueError(f"unsupported interval: {interval!r}") from None


def log_returns(close: pd.Series) -> pd.Series:
    """Continuously compounded returns. Non-positive prices are dropped."""
    close = pd.to_numeric(close, errors="coerce")
    close = close[close > 0]
    return np.log(close).diff().dropna()


def simple_returns(close: pd.Series) -> pd.Series:
    close = pd.to_numeric(close, errors="coerce")
    close = close[close > 0]
    return close.pct_change().dropna()


def total_return(close: pd.Series) -> float | None:
    """Return over the whole window, as a fraction (0.25 == +25%)."""
    close = close.dropna()
    if len(close) < 2 or close.iloc[0] <= 0:
        return None
    return float(close.iloc[-1] / close.iloc[0] - 1.0)


def cagr(close: pd.Series, interval: str) -> float | None:
    """Compound annual growth rate implied by the window."""
    close = close.dropna()
    if len(close) < 2 or close.iloc[0] <= 0:
        return None
    years = (len(close) - 1) / periods_per_year(interval)
    if years <= 0:
        return None
    growth = float(close.iloc[-1] / close.iloc[0])
    if growth <= 0:
        return None
    return growth ** (1.0 / years) - 1.0
