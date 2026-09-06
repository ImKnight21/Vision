"""Binance public market data — the primary OHLCV source.

No API key is needed for these endpoints. `data-api.binance.vision` is Binance's
own public mirror for market data and is tried first because it is not subject
to the regional blocks that make `api.binance.com` return 451 in some places.
"""

from __future__ import annotations

import pandas as pd

from app.sources.base import UpstreamError, fetch_json, to_ohlcv_frame

PROVIDER = "binance"

HOSTS = (
    "https://data-api.binance.vision",
    "https://api.binance.com",
    "https://api-gcp.binance.com",
)

# Binance's own interval vocabulary. Ours is a subset, so this is a pass-through
# guard rather than a translation table.
SUPPORTED_INTERVALS = frozenset(
    {"1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h",
     "1d", "3d", "1w"}
)

MAX_LIMIT = 1000


async def _get(path: str, params: dict | None = None):
    """Try each host in turn; raise only if every one of them fails."""
    last: Exception | None = None
    for host in HOSTS:
        try:
            return await fetch_json(PROVIDER, f"{host}{path}", params=params, attempts=2)
        except UpstreamError as exc:
            last = exc
    raise UpstreamError(PROVIDER, f"all hosts failed: {last}")


async def fetch_ohlcv(symbol: str, interval: str, limit: int = 500) -> pd.DataFrame:
    """Candles for e.g. ``BTCUSDT``, oldest-first."""
    if interval not in SUPPORTED_INTERVALS:
        raise UpstreamError(PROVIDER, f"unsupported interval {interval!r}")

    raw = await _get(
        "/api/v3/klines",
        {
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": min(max(limit, 1), MAX_LIMIT),
        },
    )
    if not isinstance(raw, list):
        raise UpstreamError(PROVIDER, "unexpected klines payload")

    # Kline layout: [openTime, o, h, l, c, volume, closeTime, quoteVolume, ...]
    rows = [
        {
            "timestamp": k[0],
            "open": k[1],
            "high": k[2],
            "low": k[3],
            "close": k[4],
            "volume": k[5],
        }
        for k in raw
    ]
    return to_ohlcv_frame(rows, source=PROVIDER)


async def fetch_tickers() -> list[dict]:
    """24h rolling stats for every USDT spot pair, normalised."""
    raw = await _get("/api/v3/ticker/24hr")
    if not isinstance(raw, list):
        raise UpstreamError(PROVIDER, "unexpected ticker payload")

    out: list[dict] = []
    for row in raw:
        symbol = row.get("symbol", "")
        if not symbol.endswith("USDT"):
            continue
        # Leveraged tokens and staked wrappers are noise in a market overview.
        base = symbol[: -len("USDT")]
        if base.endswith(("UP", "DOWN", "BULL", "BEAR")):
            continue
        try:
            quote_volume = float(row["quoteVolume"])
            last = float(row["lastPrice"])
        except (KeyError, TypeError, ValueError):
            continue
        if last <= 0 or quote_volume <= 0:
            continue
        out.append(
            {
                "symbol": symbol,
                "base": base,
                "quote": "USDT",
                "price": last,
                # Binance reports percent; we carry fractions everywhere.
                "change_24h": float(row.get("priceChangePercent", 0.0)) / 100.0,
                "high_24h": float(row.get("highPrice", 0.0)) or None,
                "low_24h": float(row.get("lowPrice", 0.0)) or None,
                "volume_24h": quote_volume,
                "trades_24h": int(row.get("count", 0)),
                "source": PROVIDER,
            }
        )

    out.sort(key=lambda r: r["volume_24h"], reverse=True)
    return out


async def fetch_symbols() -> set[str]:
    """Every actively trading USDT spot symbol."""
    raw = await _get("/api/v3/exchangeInfo", {"permissions": "SPOT"})
    symbols = raw.get("symbols", []) if isinstance(raw, dict) else []
    return {
        s["symbol"]
        for s in symbols
        if s.get("status") == "TRADING" and s.get("quoteAsset") == "USDT"
    }
