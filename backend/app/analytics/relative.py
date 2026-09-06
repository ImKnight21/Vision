"""How one asset behaves relative to another, usually BTC.

Most alts are, statistically, leveraged bets on BTC with extra noise. These
measures separate the part of a move that was simply the market from the part
that belonged to the coin, which is the difference between "it went up" and
"it outperformed".
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from app.analytics.returns import log_returns, periods_per_year


@dataclass(frozen=True)
class Relative:
    """Asset-versus-benchmark statistics over the overlapping period."""

    benchmark: str
    bars: int
    correlation: float | None
    beta: float | None
    alpha: float | None
    r_squared: float | None
    tracking_error: float | None
    up_capture: float | None
    down_capture: float | None
    relative_return: float | None

    def to_dict(self) -> dict:
        return asdict(self)


def _aligned_returns(
    asset: pd.Series, benchmark: pd.Series
) -> tuple[pd.Series, pd.Series]:
    """Log returns of both series restricted to timestamps they share.

    Aligning on the index rather than zipping is what keeps a coin with a
    shorter history, or a gap in its candles, from silently comparing bar 40 of
    one series against bar 40 of the other.
    """
    frame = pd.concat(
        {"asset": log_returns(asset), "benchmark": log_returns(benchmark)}, axis=1
    ).dropna()
    return frame["asset"], frame["benchmark"]


def compare(
    asset: pd.Series,
    benchmark: pd.Series,
    interval: str,
    benchmark_name: str = "BTCUSDT",
) -> Relative:
    """Full relative profile of `asset` against `benchmark`."""
    a, b = _aligned_returns(asset, benchmark)
    bars = len(a)

    if bars < 30:
        return Relative(benchmark_name, bars, None, None, None, None, None, None,
                        None, None)

    ppy = periods_per_year(interval)
    variance = float(b.var(ddof=1))

    correlation = float(a.corr(b)) if a.std(ddof=1) > 0 and b.std(ddof=1) > 0 else None

    if variance > 0:
        beta = float(a.cov(b) / variance)
        # Jensen's alpha: the return left over once the benchmark exposure that
        # beta describes has been paid for. Annualised.
        alpha = float((a.mean() - beta * b.mean()) * ppy)
    else:
        beta = alpha = None

    r_squared = None if correlation is None else float(correlation**2)

    # How much the asset's path deviates from the benchmark's, annualised.
    difference = a - b
    tracking_error = (
        float(difference.std(ddof=1) * np.sqrt(ppy)) if len(difference) > 1 else None
    )

    return Relative(
        benchmark=benchmark_name,
        bars=bars,
        correlation=correlation,
        beta=beta,
        alpha=alpha,
        r_squared=r_squared,
        tracking_error=tracking_error,
        up_capture=_capture(a, b, up=True),
        down_capture=_capture(a, b, up=False),
        relative_return=float(np.expm1(a.sum()) - np.expm1(b.sum())),
    )


def _capture(asset: pd.Series, benchmark: pd.Series, *, up: bool) -> float | None:
    """Share of the benchmark's move the asset captured, on its up or down bars.

    Up-capture above 1 with down-capture below 1 is the rare, desirable shape:
    it joined the rallies and sat out the falls. Both far above 1 is simply
    leverage.
    """
    mask = benchmark > 0 if up else benchmark < 0
    if mask.sum() < 10:
        return None
    benchmark_move = float(benchmark[mask].mean())
    if benchmark_move == 0:
        return None
    return float(asset[mask].mean() / benchmark_move)


def correlation_matrix(closes: dict[str, pd.Series]) -> dict:
    """Pairwise return correlations across several assets.

    Returned as an ordered symbol list plus a square matrix of the same order,
    which is what a heatmap needs and avoids the client having to reconstruct
    the ordering from nested objects.
    """
    returns = pd.DataFrame(
        {symbol: log_returns(series) for symbol, series in closes.items()}
    ).dropna()

    symbols = list(returns.columns)
    if len(returns) < 30 or len(symbols) < 2:
        return {"symbols": symbols, "bars": len(returns), "matrix": None}

    matrix = returns.corr()
    return {
        "symbols": symbols,
        "bars": len(returns),
        "matrix": [
            [None if pd.isna(value) else round(float(value), 4) for value in row]
            for row in matrix.to_numpy()
        ],
    }
