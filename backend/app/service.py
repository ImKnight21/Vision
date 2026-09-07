"""Composition layer: cache, source fallback, and the merge of price with metadata.

The routers stay thin — everything that decides *which* provider answers, and
what happens when one is down, lives here.
"""

from __future__ import annotations

import asyncio
import logging

import pandas as pd

from app.analytics import build_summary, regime, relative, risk, volatility
from app.analytics.returns import INTERVAL_SECONDS, total_return
from app.analytics.summary import bars_for_days, json_safe
from app.cache import cache
from app.config import get_settings
from app.sources import binance, bybit, coingecko, cryptocompare
from app.sources.base import UpstreamError

log = logging.getLogger("vision.service")

VALID_INTERVALS = frozenset(INTERVAL_SECONDS)

# Tried in order until one answers. Binance leads on depth and is what the
# figures are expected to match; Bybit is the keyless insurance against
# Binance's HTTP 418 IP bans, which shared hosting attracts through no fault
# of ours; CryptoCompare is last because it now demands an API key and so is
# unavailable unless one is configured.
OHLCV_SOURCES = (binance, bybit, cryptocompare)

# Only the exchanges: CryptoCompare has no equivalent whole-market ticker call.
TICKER_SOURCES = (binance, bybit)

# Almost every alt is, statistically, a leveraged position on BTC, so BTC is
# the benchmark everything is measured against by default.
BENCHMARK = "BTCUSDT"

# Comparing many symbols means one upstream call each; cap it so a crafted
# request cannot fan out into a hundred fetches.
MAX_COMPARE_SYMBOLS = 8


async def get_markets(limit: int = 100) -> list[dict]:
    """Tradable USDT pairs, ranked by market cap, with descriptive metadata.

    Binance supplies live price and volume; CoinGecko supplies name, logo and
    market cap. If CoinGecko is rate-limited we still return the Binance rows —
    a table without logos beats no table at all.
    """
    settings = get_settings()

    async def produce() -> list[dict]:
        # CoinGecko is enrichment, not the answer, so it gets a hard deadline.
        # Its client retries with backoff, which on a rate-limited free tier can
        # stack up to the better part of a minute — long enough to hold the
        # whole market list hostage for data the table renders fine without.
        async def metadata() -> list[dict]:
            # Cached under its own key, for far longer than the market list.
            # Names, logos and market caps change on a scale of days, while
            # CoinGecko's free tier rate-limits a shared hosting IP hard enough
            # that only some fetches get through: measured 3 successes in 8
            # attempts from Render, the failures arriving in under a second
            # rather than exhausting the budget. Tying metadata to the
            # two-minute market entry discarded every success within minutes
            # and made those refusals visible as a table with no logos. One
            # success now covers an hour.
            return await asyncio.wait_for(
                cache.get_or_set(
                    "coingecko:markets",
                    settings.ttl_meta,
                    lambda: coingecko.fetch_markets(per_page=250),
                ),
                timeout=settings.meta_budget,
            )

        async def prices() -> list[dict]:
            failures: list[str] = []
            for source in TICKER_SOURCES:
                try:
                    return await source.fetch_tickers()
                except UpstreamError as exc:
                    failures.append(f"{source.PROVIDER}: {exc}")
                    log.warning(
                        "%s tickers unavailable (%s); trying the next source",
                        source.PROVIDER, exc,
                    )
            raise UpstreamError(
                "vision", f"no source could list markets ({'; '.join(failures)})"
            )

        tickers, meta = await asyncio.gather(
            prices(), metadata(), return_exceptions=True
        )

        if isinstance(tickers, BaseException):
            raise tickers

        by_base: dict[str, dict] = {}
        if isinstance(meta, BaseException):
            # A bare TimeoutError stringifies to "", so name the type too.
            log.warning(
                "coingecko metadata unavailable (%s: %s); serving prices only",
                type(meta).__name__,
                meta,
            )
        else:
            # Rows arrive market-cap-desc, so the first claim on a ticker symbol
            # is the dominant coin — that is what `setdefault` keeps.
            for row in meta:
                by_base.setdefault(row["base"], row)

        merged: list[dict] = []
        for ticker in tickers:
            extra = by_base.get(ticker["base"], {})
            merged.append(
                {
                    **ticker,
                    "name": extra.get("name") or ticker["base"],
                    "image": extra.get("image"),
                    "coingecko_id": extra.get("id"),
                    "market_cap": extra.get("market_cap"),
                    "market_cap_rank": extra.get("market_cap_rank"),
                    "change_7d": extra.get("change_7d"),
                    "change_30d": extra.get("change_30d"),
                    "circulating_supply": extra.get("circulating_supply"),
                    "max_supply": extra.get("max_supply"),
                    "ath": extra.get("ath"),
                    "ath_change": extra.get("ath_change"),
                }
            )

        # Ranked coins first in rank order, then everything else by volume.
        merged.sort(
            key=lambda r: (
                r["market_cap_rank"] is None,
                r["market_cap_rank"] or 0,
                -r["volume_24h"],
            )
        )
        return merged

    rows = await cache.get_or_set("markets", settings.ttl_markets, produce)
    return rows[:limit]


async def _fetch_from_any_source(
    symbol: str, interval: str, limit: int
) -> pd.DataFrame:
    """Walk `OHLCV_SOURCES` until one answers, or report what each one said."""
    failures: list[str] = []
    for source in OHLCV_SOURCES:
        try:
            return await source.fetch_ohlcv(symbol, interval, limit)
        except UpstreamError as exc:
            failures.append(f"{source.PROVIDER}: {exc}")
            log.warning(
                "%s failed for %s %s (%s); trying the next source",
                source.PROVIDER, symbol, interval, exc,
            )
    raise UpstreamError(
        "vision",
        f"no source could serve {symbol} {interval} ({'; '.join(failures)})",
    )


async def get_ohlcv(symbol: str, interval: str, limit: int = 500) -> pd.DataFrame:
    """Candles for `symbol`, from the first source in the chain that answers."""
    if interval not in VALID_INTERVALS:
        raise ValueError(f"unsupported interval {interval!r}")

    symbol = symbol.upper()
    settings = get_settings()

    async def produce() -> pd.DataFrame:
        return await _fetch_from_any_source(symbol, interval, limit)

    return await cache.get_or_set(
        f"ohlcv:{symbol}:{interval}:{limit}", settings.ttl_ohlcv, produce
    )


async def get_latest(symbol: str, interval: str) -> dict:
    """The newest bar alone, for a chart that wants to stay current.

    Kept separate from `get_ohlcv` on purpose. That one caches for minutes
    because a settled history does not change; this bar is still forming and
    is cached for seconds. Sharing a cache entry would force a choice between
    a stale chart and refetching hundreds of bars every few seconds.

    Two bars are requested rather than one: an interval boundary can land
    between polls, and the extra bar is what lets the client draw the newly
    closed candle instead of skipping it.
    """
    if interval not in VALID_INTERVALS:
        raise ValueError(f"unsupported interval {interval!r}")

    symbol = symbol.upper()
    settings = get_settings()

    async def produce() -> dict:
        frame = await _fetch_from_any_source(symbol, interval, 2)
        return {
            "symbol": symbol,
            "interval": interval,
            "source": frame.attrs.get("source", "unknown"),
            "candles": frame_to_candles(frame),
        }

    return await cache.get_or_set(
        f"live:{symbol}:{interval}", settings.ttl_live, produce
    )


async def get_summary(symbol: str, interval: str, limit: int = 500) -> dict:
    """Every statistic for one pair, plus which provider the candles came from."""
    return (await get_overview(symbol, interval, limit))["stats"]


async def _relative_to_benchmark(
    frame: pd.DataFrame, symbol: str, interval: str, limit: int
) -> dict | None:
    """Beta, correlation and capture against BTC. None when it is meaningless.

    A failure here must not take the whole profile down: the relative block is
    an extra lens on the asset, not the asset's own statistics.
    """
    if symbol == BENCHMARK:
        return None
    try:
        benchmark = await get_ohlcv(BENCHMARK, interval, limit)
    except (UpstreamError, ValueError) as exc:
        log.warning("benchmark unavailable for %s: %s", symbol, exc)
        return None

    return relative.compare(
        frame["close"], benchmark["close"], interval, benchmark_name=BENCHMARK
    ).to_dict()


async def get_overview(symbol: str, interval: str, limit: int = 500) -> dict:
    """Candles and statistics from the same fetch.

    One round trip for the client, and both halves are guaranteed to describe
    the identical set of bars.
    """
    frame = await get_ohlcv(symbol, interval, limit)
    summary = build_summary(frame, interval, symbol.upper())
    summary["source"] = frame.attrs.get("source", "unknown")
    summary["relative"] = await _relative_to_benchmark(
        frame, symbol.upper(), interval, limit
    )
    return {
        "symbol": symbol.upper(),
        "interval": interval,
        "source": summary["source"],
        "candles": frame_to_candles(frame),
        "stats": summary,
    }


async def get_comparison(
    symbols: list[str], interval: str, limit: int = 500
) -> dict:
    """Correlation matrix plus headline stats for several coins side by side.

    Symbols that no source can serve are reported in `failed` rather than
    failing the request: one dead ticker should not blank the comparison.
    """
    if interval not in VALID_INTERVALS:
        raise ValueError(f"unsupported interval {interval!r}")

    wanted = list(dict.fromkeys(s.upper() for s in symbols if s.strip()))[
        :MAX_COMPARE_SYMBOLS
    ]
    if len(wanted) < 2:
        raise ValueError("comparison needs at least two symbols")

    frames = await asyncio.gather(
        *(get_ohlcv(s, interval, limit) for s in wanted), return_exceptions=True
    )

    closes: dict[str, pd.Series] = {}
    failed: list[str] = []
    for symbol, result in zip(wanted, frames):
        if isinstance(result, BaseException):
            log.warning("comparison dropped %s: %s", symbol, result)
            failed.append(symbol)
        else:
            closes[symbol] = result["close"]

    if len(closes) < 2:
        raise UpstreamError("vision", "fewer than two symbols could be loaded")

    benchmark = closes.get(BENCHMARK)
    window_30d = bars_for_days(30, interval)

    rows = []
    for symbol, close in closes.items():
        # Only close-based statistics here: the comparison holds price series,
        # not full bars, so the range estimators and liquidity measures have
        # nothing to read and are deliberately absent rather than faked.
        row = {
            "symbol": symbol,
            "last": json_safe(close.iloc[-1]) if len(close) else None,
            "total_return": json_safe(total_return(close)),
            "volatility_30d": json_safe(
                volatility.close_to_close(close, interval, window_30d)
            ),
            "sharpe": json_safe(risk.sharpe_ratio(close, interval)),
            "max_drawdown": json_safe(risk.analyse_drawdown(close).max_drawdown),
            "hurst": json_safe(regime.hurst_exponent(close)),
        }
        if benchmark is not None and symbol != BENCHMARK:
            stats = relative.compare(close, benchmark, interval, BENCHMARK)
            row |= {
                "beta": stats.beta,
                "correlation": stats.correlation,
                "alpha": stats.alpha,
            }
        else:
            row |= {"beta": None, "correlation": None, "alpha": None}
        rows.append(row)

    return {
        "interval": interval,
        "benchmark": BENCHMARK if benchmark is not None else None,
        "failed": failed,
        "rows": rows,
        **relative.correlation_matrix(closes),
    }


def frame_to_candles(frame: pd.DataFrame) -> list[dict]:
    """Serialise a frame for the chart: seconds since epoch, plain floats."""
    return [
        {
            # lightweight-charts wants UNIX seconds, not milliseconds.
            "time": int(timestamp.timestamp()),
            "open": None if pd.isna(row.open) else float(row.open),
            "high": None if pd.isna(row.high) else float(row.high),
            "low": None if pd.isna(row.low) else float(row.low),
            "close": None if pd.isna(row.close) else float(row.close),
            "volume": None if pd.isna(row.volume) else float(row.volume),
        }
        for timestamp, row in zip(frame.index, frame.itertuples(index=False))
    ]
