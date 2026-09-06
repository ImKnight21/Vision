"""Bybit public market data — the keyless fallback for candles and tickers.

Binance is primary, but it bans an IP with HTTP 418 once that address exceeds
its request weight, and shared hosting egresses through addresses many other
tenants are also hammering. When that happens every Binance call fails for
reasons that have nothing to do with this application, so there has to be a
second source that needs no credentials.

Bybit is that source because it speaks the same dialect: spot symbols are
``BTCUSDT``, exactly as on Binance, so substituting it needs no ticker
translation table. Coinbase (``BTC-USD``) and OKX (``BTC-USDT``) would each
require one, and a translation table is a second thing to get wrong.

Prices come from a different order book than Binance's, so the two will not
agree tick for tick. Over a statistical window that difference is immaterial;
for execution it would not be.
"""

from __future__ import annotations

import pandas as pd

from app.sources.base import UpstreamError, fetch_json, is_leveraged, to_ohlcv_frame

PROVIDER = "bybit"

HOST = "https://api.bybit.com"

# Bybit counts minutes as bare numbers and switches to letters at a day.
# `3d` has no equivalent, so it is absent rather than approximated.
INTERVAL_MAP: dict[str, str] = {
    "1m": "1",
    "3m": "3",
    "5m": "5",
    "15m": "15",
    "30m": "30",
    "1h": "60",
    "2h": "120",
    "4h": "240",
    "6h": "360",
    "12h": "720",
    "1d": "D",
    "1w": "W",
}

MAX_LIMIT = 1000


async def _get(path: str, params: dict | None = None) -> dict:
    """GET and unwrap Bybit's envelope.

    Bybit answers HTTP 200 even when the call failed, putting the real outcome
    in `retCode`. Left unchecked that turns an upstream error into an empty
    candle list, so the envelope is enforced here.
    """
    raw = await fetch_json(PROVIDER, f"{HOST}{path}", params=params, attempts=2)
    if not isinstance(raw, dict):
        raise UpstreamError(PROVIDER, "unexpected payload")
    if raw.get("retCode") != 0:
        raise UpstreamError(PROVIDER, f"retCode {raw.get('retCode')}: {raw.get('retMsg')}")
    result = raw.get("result")
    if not isinstance(result, dict):
        raise UpstreamError(PROVIDER, "response carried no result")
    return result


async def fetch_ohlcv(symbol: str, interval: str, limit: int = 500) -> pd.DataFrame:
    """Candles for e.g. ``BTCUSDT``, oldest-first."""
    mapped = INTERVAL_MAP.get(interval)
    if mapped is None:
        raise UpstreamError(PROVIDER, f"unsupported interval {interval!r}")

    result = await _get(
        "/v5/market/kline",
        {
            "category": "spot",
            "symbol": symbol.upper(),
            "interval": mapped,
            "limit": min(max(limit, 1), MAX_LIMIT),
        },
    )
    candles = result.get("list")
    if not isinstance(candles, list):
        raise UpstreamError(PROVIDER, "unexpected kline payload")

    # Layout: [startTime, open, high, low, close, volume, turnover], newest
    # first. `to_ohlcv_frame` sorts by timestamp, so the order needs no fixing.
    rows = [
        {
            "timestamp": int(k[0]),
            "open": k[1],
            "high": k[2],
            "low": k[3],
            "close": k[4],
            "volume": k[5],
        }
        for k in candles
        if len(k) >= 6
    ]
    return to_ohlcv_frame(rows, source=PROVIDER)


async def fetch_tickers() -> list[dict]:
    """24h rolling stats for every USDT spot pair, normalised."""
    result = await _get("/v5/market/tickers", {"category": "spot"})
    rows = result.get("list")
    if not isinstance(rows, list):
        raise UpstreamError(PROVIDER, "unexpected ticker payload")

    traded_bases = {
        row["symbol"][: -len("USDT")]
        for row in rows
        if isinstance(row.get("symbol"), str) and row["symbol"].endswith("USDT")
    }

    out: list[dict] = []
    for row in rows:
        symbol = row.get("symbol", "")
        if not symbol.endswith("USDT"):
            continue
        base = symbol[: -len("USDT")]
        if is_leveraged(base, traded_bases):
            continue
        try:
            last = float(row["lastPrice"])
            # `turnover24h` is quote volume, the same measure as Binance's
            # `quoteVolume`; `volume24h` is base volume and would not compare.
            quote_volume = float(row["turnover24h"])
        except (KeyError, TypeError, ValueError):
            continue
        if last <= 0 or quote_volume <= 0:
            continue

        def optional(field: str) -> float | None:
            try:
                return float(row[field]) or None
            except (KeyError, TypeError, ValueError):
                return None

        out.append(
            {
                "symbol": symbol,
                "base": base,
                "quote": "USDT",
                "price": last,
                # Already a fraction, unlike Binance's percent. Dividing here
                # would quietly report every move as a hundredth of itself.
                "change_24h": optional("price24hPcnt") or 0.0,
                "high_24h": optional("highPrice24h"),
                "low_24h": optional("lowPrice24h"),
                "volume_24h": quote_volume,
                # Bybit does not publish a trade count for spot.
                "trades_24h": None,
                "source": PROVIDER,
            }
        )

    out.sort(key=lambda r: r["volume_24h"], reverse=True)
    return out
