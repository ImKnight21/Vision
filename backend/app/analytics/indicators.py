"""Classic technical indicators, computed with Wilder's smoothing where that is
the conventional definition (RSI, ATR) so the numbers match other terminals."""

from __future__ import annotations

import numpy as np
import pandas as pd


def sma(close: pd.Series, window: int) -> pd.Series:
    return close.rolling(window).mean()


def ema(close: pd.Series, span: int) -> pd.Series:
    return close.ewm(span=span, adjust=False).mean()


def true_range(frame: pd.DataFrame) -> pd.Series:
    """The greater of the bar's own range and its gap from the prior close."""
    prev_close = frame["close"].shift(1)
    ranges = pd.concat(
        [
            frame["high"] - frame["low"],
            (frame["high"] - prev_close).abs(),
            (frame["low"] - prev_close).abs(),
        ],
        axis=1,
    )
    return ranges.max(axis=1)


def atr(frame: pd.DataFrame, window: int = 14) -> pd.Series:
    """Average True Range, Wilder-smoothed. Absolute price units."""
    # alpha = 1/window reproduces Wilder's smoothing; a plain EMA would use
    # 2/(window+1) and read noticeably hotter.
    return true_range(frame).ewm(alpha=1.0 / window, adjust=False).mean()


def atr_percent(frame: pd.DataFrame, window: int = 14) -> pd.Series:
    """ATR as a share of price, so it can be compared across coins."""
    return atr(frame, window) / frame["close"]


def rsi(close: pd.Series, window: int = 14) -> pd.Series:
    """Relative Strength Index, 0-100. Above 70 is conventionally 'overbought'."""
    delta = close.diff()
    gains = delta.clip(lower=0.0)
    losses = (-delta).clip(lower=0.0)
    avg_gain = gains.ewm(alpha=1.0 / window, adjust=False).mean()
    avg_loss = losses.ewm(alpha=1.0 / window, adjust=False).mean()
    # A window with no losses is RSI 100 by definition, not a division by zero.
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    result = 100.0 - 100.0 / (1.0 + rs)
    return result.where(avg_loss != 0.0, 100.0).where(avg_gain != 0.0, 0.0)


def bollinger(
    close: pd.Series, window: int = 20, num_std: float = 2.0
) -> pd.DataFrame:
    """Bands, their width, and where price sits inside them (%B)."""
    mid = close.rolling(window).mean()
    std = close.rolling(window).std(ddof=1)
    upper = mid + num_std * std
    lower = mid - num_std * std
    span = (upper - lower).replace(0.0, np.nan)
    return pd.DataFrame(
        {
            "middle": mid,
            "upper": upper,
            "lower": lower,
            # Width normalised by the mid, so it is comparable across coins.
            "width": (upper - lower) / mid.replace(0.0, np.nan),
            "percent_b": (close - lower) / span,
        }
    )


def range_position(close: pd.Series, window: int | None = None) -> dict[str, float | None]:
    """Where the latest close sits between the window's low and high (0..1)."""
    series = close.dropna()
    if window is not None:
        series = series.tail(window)
    if len(series) < 2:
        return {"high": None, "low": None, "position": None}
    high = float(series.max())
    low = float(series.min())
    last = float(series.iloc[-1])
    span = high - low
    return {
        "high": high,
        "low": low,
        "position": float((last - low) / span) if span > 0 else None,
    }
