"""CoinGecko — market capitalisation, coin metadata and logos.

Binance knows prices but not what a coin *is*: no name, no market cap, no logo,
and no coverage of anything it does not list. CoinGecko fills that in. The free
tier is tightly rate-limited, so every call here goes through the TTL cache.
"""

from __future__ import annotations

import pandas as pd

from app.config import get_settings
from app.sources.base import UpstreamError, fetch_json, to_ohlcv_frame

PROVIDER = "coingecko"

PUBLIC_HOST = "https://api.coingecko.com/api/v3"
PRO_HOST = "https://pro-api.coingecko.com/api/v3"


def _host_and_headers() -> tuple[str, dict]:
    """Demo keys go to the public host; both key styles use their own header."""
    key = get_settings().coingecko_api_key.strip()
    if not key:
        return PUBLIC_HOST, {}
    if key.startswith("CG-"):
        return PUBLIC_HOST, {"x-cg-demo-api-key": key}
    return PRO_HOST, {"x-cg-pro-api-key": key}


async def _get(path: str, params: dict | None = None):
    host, headers = _host_and_headers()
    return await fetch_json(PROVIDER, f"{host}{path}", params=params, headers=headers)


async def fetch_markets(per_page: int = 250, page: int = 1) -> list[dict]:
    """Top coins by market cap, with the descriptive fields Binance lacks."""
    raw = await _get(
        "/coins/markets",
        {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": min(max(per_page, 1), 250),
            "page": page,
            "sparkline": "false",
            "price_change_percentage": "24h,7d,30d",
        },
    )
    if not isinstance(raw, list):
        raise UpstreamError(PROVIDER, "unexpected markets payload")

    def pct(value) -> float | None:
        return None if value is None else float(value) / 100.0

    return [
        {
            "id": row.get("id"),
            "base": (row.get("symbol") or "").upper(),
            "name": row.get("name"),
            "image": row.get("image"),
            "price": row.get("current_price"),
            "market_cap": row.get("market_cap"),
            "market_cap_rank": row.get("market_cap_rank"),
            "volume_24h": row.get("total_volume"),
            "circulating_supply": row.get("circulating_supply"),
            "total_supply": row.get("total_supply"),
            "max_supply": row.get("max_supply"),
            "ath": row.get("ath"),
            "ath_change": pct(row.get("ath_change_percentage")),
            "ath_date": row.get("ath_date"),
            "atl": row.get("atl"),
            "atl_date": row.get("atl_date"),
            "change_24h": pct(row.get("price_change_percentage_24h_in_currency")),
            "change_7d": pct(row.get("price_change_percentage_7d_in_currency")),
            "change_30d": pct(row.get("price_change_percentage_30d_in_currency")),
            "source": PROVIDER,
        }
        for row in raw
        if row.get("symbol")
    ]


async def fetch_ohlc(coin_id: str, days: int = 365) -> pd.DataFrame:
    """OHLC candles for a coin id. No volume — CoinGecko's /ohlc omits it.

    Candle width is chosen by CoinGecko from `days` (1-2d -> 30m, 3-30d -> 4h,
    31d+ -> 4d), so this is a coverage fallback, not an interval-accurate feed.
    """
    allowed = (1, 7, 14, 30, 90, 180, 365)
    days = min(allowed, key=lambda d: abs(d - days))

    raw = await _get(f"/coins/{coin_id}/ohlc", {"vs_currency": "usd", "days": days})
    if not isinstance(raw, list):
        raise UpstreamError(PROVIDER, "unexpected ohlc payload")

    rows = [
        {"timestamp": c[0], "open": c[1], "high": c[2], "low": c[3], "close": c[4],
         "volume": None}
        for c in raw
    ]
    return to_ohlcv_frame(rows, source=PROVIDER)
