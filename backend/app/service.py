"""Composition layer: cache, source fallback, and the merge of price with metadata.

The routers stay thin — everything that decides *which* provider answers, and
what happens when one is down, lives here.
"""

from __future__ import annotations

import asyncio
import logging

import pandas as pd

from app.analytics import build_summary
from app.analytics.returns import INTERVAL_SECONDS
from app.cache import cache
from app.config import get_settings
from app.sources import binance, coingecko, cryptocompare
from app.sources.base import UpstreamError

log = logging.getLogger("vision.service")

VALID_INTERVALS = frozenset(INTERVAL_SECONDS)


async def get_markets(limit: int = 100) -> list[dict]:
    """Tradable USDT pairs, ranked by market cap, with descriptive metadata.

    Binance supplies live price and volume; CoinGecko supplies name, logo and
    market cap. If CoinGecko is rate-limited we still return the Binance rows —
    a table without logos beats no table at all.
    """
    settings = get_settings()

    async def produce() -> list[dict]:
        tickers, meta = await asyncio.gather(
            binance.fetch_tickers(),
            coingecko.fetch_markets(per_page=250),
            return_exceptions=True,
        )

        if isinstance(tickers, BaseException):
            raise tickers

        by_base: dict[str, dict] = {}
        if isinstance(meta, BaseException):
            log.warning("coingecko metadata unavailable: %s", meta)
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


async def get_ohlcv(symbol: str, interval: str, limit: int = 500) -> pd.DataFrame:
    """Candles for `symbol`, falling back to CryptoCompare if Binance fails."""
    if interval not in VALID_INTERVALS:
        raise ValueError(f"unsupported interval {interval!r}")

    symbol = symbol.upper()
    settings = get_settings()

    async def produce() -> pd.DataFrame:
        try:
            return await binance.fetch_ohlcv(symbol, interval, limit)
        except UpstreamError as exc:
            log.warning("binance failed for %s %s (%s); trying fallback",
                        symbol, interval, exc)
            try:
                return await cryptocompare.fetch_ohlcv(symbol, interval, limit)
            except UpstreamError as fallback_exc:
                # Surface the primary failure: it is the one worth acting on.
                raise UpstreamError(
                    "vision",
                    f"no source could serve {symbol} {interval} "
                    f"(binance: {exc}; cryptocompare: {fallback_exc})",
                ) from fallback_exc

    return await cache.get_or_set(
        f"ohlcv:{symbol}:{interval}:{limit}", settings.ttl_ohlcv, produce
    )


async def get_summary(symbol: str, interval: str, limit: int = 500) -> dict:
    """Every statistic for one pair, plus which provider the candles came from."""
    frame = await get_ohlcv(symbol, interval, limit)
    summary = build_summary(frame, interval, symbol.upper())
    summary["source"] = frame.attrs.get("source", "unknown")
    return summary


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
