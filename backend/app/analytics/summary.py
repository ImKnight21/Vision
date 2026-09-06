"""Assemble every statistic into one JSON-safe payload for the API."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

from app.analytics import indicators, liquidity, regime, risk, volatility
from app.analytics.returns import INTERVAL_SECONDS, cagr, total_return

# Lookbacks are expressed in calendar days and converted to bars, so "30d
# volatility" means the same span of time whether the chart is hourly or daily.
WINDOW_DAYS: tuple[int, ...] = (7, 30, 90)


def json_safe(value: Any) -> Any:
    """NaN and infinity are not valid JSON; send null instead.

    Public because the comparison endpoint assembles its own rows and needs the
    same guarantee.
    """
    if value is None:
        return None
    if isinstance(value, (int, str, bool)):
        return value
    number = float(value)
    return None if math.isnan(number) or math.isinf(number) else number


def _last(series: pd.Series) -> float | None:
    series = series.dropna()
    return json_safe(series.iloc[-1]) if len(series) else None


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
    return json_safe(float(close.iloc[-1]) / past - 1.0)


def bars_to_days(bars: int | None, interval: str) -> float | None:
    """Express a bar count as calendar days, which is how durations are read."""
    if bars is None:
        return None
    return round(bars * INTERVAL_SECONDS[interval] / 86_400, 2)


def _windowed(fn, *args, interval: str, **kwargs) -> dict[str, float | None]:
    """Run an estimator over each lookback, skipping windows we cannot fill."""
    out: dict[str, float | None] = {}
    series_len = len(args[0])
    for days in WINDOW_DAYS:
        bars = bars_for_days(days, interval)
        # Demand the full window: a "90d" number built from 12 bars would be
        # labelled honestly but read as if it carried the same weight.
        out[f"{days}d"] = (
            json_safe(fn(*args, interval, window=bars, **kwargs))
            if series_len >= bars
            else None
        )
    # An all-history figure is always available and never misleading.
    out["all"] = json_safe(fn(*args, interval, window=None, **kwargs))
    return out


def build_summary(frame: pd.DataFrame, interval: str, symbol: str) -> dict[str, Any]:
    """Full statistical profile of one OHLCV series.

    `frame` must be indexed by UTC timestamp with open/high/low/close/volume
    columns, sorted oldest-first.
    """
    close = frame["close"].astype(float)
    bars = len(frame)

    drawdown = risk.analyse_drawdown(close)
    underwater = risk.time_under_water(close)
    dollar_volume = liquidity.dollar_volume_stats(frame)
    bands = indicators.bollinger(close)

    return {
        "symbol": symbol,
        "interval": interval,
        "bars": bars,
        "period_start": frame.index[0].isoformat() if bars else None,
        "period_end": frame.index[-1].isoformat() if bars else None,
        "price": {
            "last": json_safe(close.iloc[-1]) if bars else None,
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
            "total": json_safe(total_return(close)),
            "cagr": json_safe(cagr(close, interval)),
        },
        "volatility": {
            # Annualised fractions: 0.65 means 65% a year.
            "realized": _windowed(volatility.close_to_close, close, interval=interval),
            "parkinson": _windowed(volatility.parkinson, frame, interval=interval),
            "garman_klass": _windowed(volatility.garman_klass, frame, interval=interval),
            "rogers_satchell": _windowed(
                volatility.rogers_satchell, frame, interval=interval
            ),
            "ewma": json_safe(volatility.ewma(close, interval)),
        },
        "risk": {
            "sharpe": json_safe(risk.sharpe_ratio(close, interval)),
            "sortino": json_safe(risk.sortino_ratio(close, interval)),
            "calmar": json_safe(risk.calmar_ratio(close, interval)),
            "max_drawdown": json_safe(drawdown.max_drawdown),
            "current_drawdown": json_safe(drawdown.current_drawdown),
            "drawdown_peak_at": drawdown.peak_at.isoformat() if drawdown.peak_at is not None else None,
            "drawdown_trough_at": drawdown.trough_at.isoformat() if drawdown.trough_at is not None else None,
            "drawdown_recovered_at": drawdown.recovered_at.isoformat() if drawdown.recovered_at is not None else None,
            "var_95": json_safe(risk.value_at_risk(close, 0.95)),
            "cvar_95": json_safe(risk.conditional_value_at_risk(close, 0.95)),
            "var_99": json_safe(risk.value_at_risk(close, 0.99)),
            "cvar_99": json_safe(risk.conditional_value_at_risk(close, 0.99)),
            # Depth alone undersells a slump that lasted a year, so these
            # measure how long the asset spent below its high as well.
            "ulcer_index": json_safe(risk.ulcer_index(close)),
            "underwater_share": json_safe(underwater["share"]),
            "underwater_longest_days": bars_to_days(underwater["longest_bars"], interval),
            "underwater_current_days": bars_to_days(underwater["current_bars"], interval),
            "recovery_factor": json_safe(risk.recovery_factor(close)),
            "tail_ratio": json_safe(risk.tail_ratio(close)),
            "omega": json_safe(risk.omega_ratio(close)),
            "gain_to_pain": json_safe(risk.gain_to_pain(close)),
        },
        "regime": {
            # Above 0.5 trends, below 0.5 mean-reverts, 0.5 is a random walk.
            "hurst": json_safe(regime.hurst_exponent(close)),
            "autocorrelation": json_safe(regime.autocorrelation(close)),
            "vol_of_vol": json_safe(regime.volatility_of_volatility(close, interval)),
            "vol_percentile": json_safe(regime.volatility_percentile(close, interval)),
            "trend_strength": json_safe(regime.trend_strength(close)),
            "trend_change": json_safe(regime.trend_change(close)),
        },
        "liquidity": {
            "amihud": json_safe(liquidity.amihud_illiquidity(frame)),
            "volume_zscore": json_safe(liquidity.volume_zscore(frame)),
            "volume_trend": json_safe(liquidity.volume_trend(frame)),
            "dollar_volume_median": json_safe(dollar_volume["median"]),
            "dollar_volume_min": json_safe(dollar_volume["min"]),
        },
        "distribution": {k: json_safe(v) for k, v in risk.return_distribution(close).items()},
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
