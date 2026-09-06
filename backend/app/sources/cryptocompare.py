"""CryptoCompare — the OHLCV fallback when Binance has no pair or is unreachable.

Prices here are aggregated across exchanges rather than taken from one book, so
they will not tick-for-tick match Binance. That is acceptable for statistics
over a window; it would not be for execution.
"""

from __future__ import annotations

import pandas as pd

from app.config import get_settings
from app.sources.base import UpstreamError, fetch_json, to_ohlcv_frame

PROVIDER = "cryptocompare"
HOST = "https://min-api.cryptocompare.com/data/v2"

# CryptoCompare offers three endpoints and an aggregation factor, so a 4h bar is
# "histohour aggregated 4". Maps our interval to (endpoint, aggregate).
INTERVAL_MAP: dict[str, tuple[str, int]] = {
    "1m": ("histominute", 1),
    "5m": ("histominute", 5),
    "15m": ("histominute", 15),
    "30m": ("histominute", 30),
    "1h": ("histohour", 1),
    "2h": ("histohour", 2),
    "4h": ("histohour", 4),
    "6h": ("histohour", 6),
    "12h": ("histohour", 12),
    "1d": ("histoday", 1),
    "3d": ("histoday", 3),
    "1w": ("histoday", 7),
}

MAX_LIMIT = 2000


def _headers() -> dict:
    key = get_settings().cryptocompare_api_key.strip()
    return {"authorization": f"Apikey {key}"} if key else {}


async def fetch_ohlcv(symbol: str, interval: str, limit: int = 500) -> pd.DataFrame:
    """Candles for a Binance-style symbol such as ``BTCUSDT``.

    USDT is requested as USD: CryptoCompare's USD series is far deeper, and the
    two differ by the stablecoin's peg deviation, which is negligible here.
    """
    if interval not in INTERVAL_MAP:
        raise UpstreamError(PROVIDER, f"unsupported interval {interval!r}")

    base, quote = _split_symbol(symbol)
    endpoint, aggregate = INTERVAL_MAP[interval]

    payload = await fetch_json(
        PROVIDER,
        f"{HOST}/{endpoint}",
        params={
            "fsym": base,
            "tsym": "USD" if quote in {"USDT", "USDC", "BUSD"} else quote,
            "aggregate": aggregate,
            # The API returns limit+1 candles; ask for one fewer.
            "limit": min(max(limit, 2), MAX_LIMIT) - 1,
        },
        headers=_headers(),
    )

    if payload.get("Response") == "Error":
        raise UpstreamError(PROVIDER, payload.get("Message", "unknown error"))

    candles = (payload.get("Data") or {}).get("Data") or []
    rows = [
        {
            "timestamp": c["time"] * 1000,  # seconds -> milliseconds
            "open": c.get("open"),
            "high": c.get("high"),
            "low": c.get("low"),
            "close": c.get("close"),
            # volumefrom is denominated in the base asset, matching Binance's
            # base volume more closely than volumeto would.
            "volume": c.get("volumefrom"),
        }
        for c in candles
    ]
    frame = to_ohlcv_frame(rows, source=PROVIDER)
    # CryptoCompare pads the start of a short history with all-zero candles.
    return frame[frame["close"] > 0]


def _split_symbol(symbol: str) -> tuple[str, str]:
    """Split ``BTCUSDT`` into ``("BTC", "USDT")``."""
    symbol = symbol.upper()
    for quote in ("USDT", "USDC", "BUSD", "USD", "BTC", "ETH", "EUR"):
        if symbol.endswith(quote) and len(symbol) > len(quote):
            return symbol[: -len(quote)], quote
    raise UpstreamError(PROVIDER, f"cannot parse symbol {symbol!r}")
