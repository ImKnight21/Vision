"""Assemble every statistic into one JSON-safe payload for the API."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

from app.analytics import indicators, risk, volatility
from app.analytics.returns import INTERVAL_SECONDS, cagr, total_return

# Lookbacks are expressed in calendar days and converted to bars, so "30d
# volatility" means the same span of time whether the chart is hourly or daily.
WINDOW_DAYS: tuple[int, ...] = (7, 30, 90)


def _clean(value: Any) -> Any:
    """NaN and infinity are not valid JSON; send null instead."""
    if value is None:
        return None
    if isinstance(value, (int, str, bool)):
        return value
    number = float(value)
    return None if math.isnan(number) or math.isinf(number) else number


def _last(series: pd.Series) -> float | None:
    series = series.dropna()
    return _clean(series.iloc[-1]) if len(series) else None


def bars_for_days(days: int, interval: str) -> int:
    """How many bars of `interval` span `days` calendar days."""
    return max(1, round(days * 86_400 / INTERVAL_SECONDS[interval]))


def _change_over(close: pd.Series, days: int, interval: str) -> float | None:
    """Fractional price change over the trailing `days`, or None if too short."""
    bars = bars_for_days(days, interval)
    if len(close) <= bars:
        return None
    past = float(close.iloc[-1 - bars])
    if past <= 0:
        return None
    return _clean(float(close.iloc[-1]) / past - 1.0)


def _windowed(fn, *args, interval: str, **kwargs) -> dict[str, float | None]:
    """Run an estimator over each lookback, skipping windows we cannot fill."""
    out: dict[str, float | None] = {}
    series_len = len(args[0])
    for days in WINDOW_DAYS:
        bars = bars_for_days(days, interval)
        # Demand the full window: a "90d" number built from 12 bars would be
        # labelled honestly but read as if it carried the same weight.
        out[f"{days}d"] = (
            _clean(fn(*args, interval, window=bars, **kwargs))
            if series_len >= bars
            else None
        )
    # An all-history figure is always available and never misleading.
    out["all"] = _clean(fn(*args, interval, window=None, **kwargs))
    return out


def build_summary(frame: pd.DataFrame, interval: str, symbol: str) -> dict[str, Any]:
    """Full statistical profile of one OHLCV series.

    `frame` must be indexed by UTC timestamp with open/high/low/close/volume
    columns, sorted oldest-first.
    """
    close = frame["close"].astype(float)
    bars = len(frame)

    drawdown = risk.analyse_drawdown(close)
    bands = indicators.bollinger(close)

    return {
        "symbol": symbol,
        "interval": interval,
        "bars": bars,
        "period_start": frame.index[0].isoformat() if bars else None,
        "period_end": frame.index[-1].isoformat() if bars else None,
        "price": {
            "last": _clean(close.iloc[-1]) if bars else None,
            "change_1d": _change_over(close, 1, interval),
            "change_7d": _change_over(close, 7, interval),
            "change_30d": _change_over(close, 30, interval),
            "change_90d": _change_over(close, 90, interval),
            **{
                f"range_{days}d": indicators.range_position(
                    close, bars_for_days(days, interval)
                )
                for days in (30, 365)
            },
        },
        "returns": {
            "total": _clean(total_return(close)),
            "cagr": _clean(cagr(close, interval)),
        },
        "volatility": {
            # Annualised fractions: 0.65 means 65% a year.
            "realized": _windowed(volatility.close_to_close, close, interval=interval),
            "parkinson": _windowed(volatility.parkinson, frame, interval=interval),
            "garman_klass": _windowed(volatility.garman_klass, frame, interval=interval),
            "rogers_satchell": _windowed(
                volatility.rogers_satchell, frame, interval=interval
            ),
            "ewma": _clean(volatility.ewma(close, interval)),
        },
        "risk": {
            "sharpe": _clean(risk.sharpe_ratio(close, interval)),
            "sortino": _clean(risk.sortino_ratio(close, interval)),
            "calmar": _clean(risk.calmar_ratio(close, interval)),
            "max_drawdown": _clean(drawdown.max_drawdown),
            "current_drawdown": _clean(drawdown.current_drawdown),
            "drawdown_peak_at": drawdown.peak_at.isoformat() if drawdown.peak_at is not None else None,
            "drawdown_trough_at": drawdown.trough_at.isoformat() if drawdown.trough_at is not None else None,
            "drawdown_recovered_at": drawdown.recovered_at.isoformat() if drawdown.recovered_at is not None else None,
            "var_95": _clean(risk.value_at_risk(close, 0.95)),
            "cvar_95": _clean(risk.conditional_value_at_risk(close, 0.95)),
            "var_99": _clean(risk.value_at_risk(close, 0.99)),
            "cvar_99": _clean(risk.conditional_value_at_risk(close, 0.99)),
        },
        "distribution": {k: _clean(v) for k, v in risk.return_distribution(close).items()},
        "indicators": {
            "rsi_14": _last(indicators.rsi(close)),
            "atr_14": _last(indicators.atr(frame)),
            "atr_percent_14": _last(indicators.atr_percent(frame)),
            "sma_20": _last(indicators.sma(close, 20)),
            "sma_50": _last(indicators.sma(close, 50)),
            "sma_200": _last(indicators.sma(close, 200)),
            "ema_12": _last(indicators.ema(close, 12)),
            "ema_26": _last(indicators.ema(close, 26)),
            "bollinger_width": _last(bands["width"]),
            "percent_b": _last(bands["percent_b"]),
        },
    }
