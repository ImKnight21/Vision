"""Liquidity measures.

Volatility describes the price you see. Liquidity describes whether you could
have traded at it. For a large-cap the distinction rarely bites; for a thin alt
it is often the whole risk, and it is the dimension a returns-only view misses.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.analytics.returns import simple_returns


def quote_volume(frame: pd.DataFrame) -> pd.Series:
    """Volume valued in the quote currency, i.e. roughly dollars traded.

    Binance klines report base-asset volume, so a coin worth $0.02 and one
    worth $70,000 are not comparable until this multiplication happens.
    """
    return frame["volume"].astype(float) * frame["close"].astype(float)


def amihud_illiquidity(frame: pd.DataFrame, window: int = 30) -> float | None:
    """Amihud's measure: average price impact per unit of dollar volume.

    Scaled so the result reads as *the fractional price move caused by $1M of
    volume*: 0.0001 means a million dollars traded moves the price about 0.01%.
    Higher means thinner. A large cap sits near zero; a thin alt can be four
    orders of magnitude above it.

    Compare it across coins, not against an absolute threshold.
    """
    returns = simple_returns(frame["close"]).abs()
    dollars = quote_volume(frame).reindex(returns.index)

    combined = pd.concat([returns, dollars], axis=1).dropna()
    combined = combined[combined.iloc[:, 1] > 0].tail(window)
    if len(combined) < max(5, window // 3):
        return None

    impact = combined.iloc[:, 0] / combined.iloc[:, 1]
    return float(impact.mean() * 1e6)


def volume_zscore(frame: pd.DataFrame, window: int = 30) -> float | None:
    """How unusual the latest bar's turnover is, in standard deviations.

    Above +2 means a volume spike, which gives a price move corroboration; a
    breakout on below-average volume is the one to distrust.
    """
    dollars = quote_volume(frame).dropna().tail(window + 1)
    if len(dollars) < max(10, window // 2):
        return None

    history = dollars.iloc[:-1]
    deviation = float(history.std(ddof=1))
    if deviation == 0:
        return None
    return float((float(dollars.iloc[-1]) - float(history.mean())) / deviation)


def volume_trend(frame: pd.DataFrame, short: int = 7, long: int = 30) -> float | None:
    """Recent average turnover over its longer-run average.

    Above 1 means participation is picking up. Sustained readings below 1 during
    a price rise mean the move is running on fewer and fewer participants.
    """
    dollars = quote_volume(frame).dropna()
    if len(dollars) < long:
        return None
    long_mean = float(dollars.tail(long).mean())
    if long_mean <= 0:
        return None
    return float(dollars.tail(short).mean() / long_mean)


def turnover(frame: pd.DataFrame, market_cap: float | None) -> float | None:
    """Latest bar's dollar volume as a share of market capitalisation.

    A coin turning over a large fraction of itself daily is either genuinely
    liquid or being churned; either way it behaves differently from one whose
    float barely moves.
    """
    if not market_cap or market_cap <= 0:
        return None
    dollars = quote_volume(frame).dropna()
    if dollars.empty:
        return None
    return float(dollars.iloc[-1] / market_cap)


def dollar_volume_stats(frame: pd.DataFrame, window: int = 30) -> dict[str, float | None]:
    """Typical and worst-case turnover over the window, in quote currency."""
    dollars = quote_volume(frame).dropna().tail(window)
    if dollars.empty:
        return {"median": None, "min": None}
    return {
        # The median, not the mean: one listing-day spike should not describe
        # what an ordinary day looks like.
        "median": float(np.median(dollars.to_numpy(dtype=float))),
        "min": float(dollars.min()),
    }
