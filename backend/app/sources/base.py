"""Shared HTTP plumbing for the data adapters."""

from __future__ import annotations

import asyncio
import logging

import httpx
import pandas as pd

from app.config import get_settings

log = logging.getLogger("vision.sources")

OHLCV_COLUMNS = ["open", "high", "low", "close", "volume"]

_client: httpx.AsyncClient | None = None


class UpstreamError(RuntimeError):
    """An upstream provider failed or answered with something unusable."""

    def __init__(self, provider: str, message: str, status: int | None = None) -> None:
        super().__init__(f"{provider}: {message}")
        self.provider = provider
        self.status = status


async def get_client() -> httpx.AsyncClient:
    """One pooled client for the process; connections are reused across calls."""
    global _client
    if _client is None or _client.is_closed:
        settings = get_settings()
        _client = httpx.AsyncClient(
            timeout=settings.http_timeout,
            headers={"User-Agent": "Vision/0.1 (+https://github.com/ImKnight21/Vision)"},
            follow_redirects=True,
        )
    return _client


async def close_client() -> None:
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
    _client = None


async def fetch_json(
    provider: str,
    url: str,
    *,
    params: dict | None = None,
    headers: dict | None = None,
    attempts: int = 3,
):
    """GET JSON, retrying on timeouts, 429s and 5xx with exponential backoff.

    4xx other than 429 are not retried: they will fail identically next time.
    """
    client = await get_client()
    last: Exception | None = None

    for attempt in range(attempts):
        try:
            response = await client.get(url, params=params, headers=headers)
            if response.status_code == 429 or response.status_code >= 500:
                raise UpstreamError(
                    provider,
                    f"HTTP {response.status_code}",
                    status=response.status_code,
                )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            raise UpstreamError(
                provider, f"HTTP {exc.response.status_code}", exc.response.status_code
            ) from exc
        except (httpx.TransportError, UpstreamError) as exc:
            last = exc
            if attempt == attempts - 1:
                break
            backoff = 0.5 * 2**attempt
            log.warning("%s attempt %d/%d failed (%s); retrying in %.1fs",
                        provider, attempt + 1, attempts, exc, backoff)
            await asyncio.sleep(backoff)

    raise UpstreamError(provider, f"unreachable after {attempts} attempts: {last}")


def to_ohlcv_frame(rows: list[dict], *, source: str) -> pd.DataFrame:
    """Normalise adapter rows into the canonical frame.

    Rows need a UTC-ms `timestamp` plus the OHLCV fields. The result is sorted
    oldest-first, deduplicated, and free of rows with a missing close.
    """
    if not rows:
        raise UpstreamError(source, "no candles returned")

    frame = pd.DataFrame(rows)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], unit="ms", utc=True)
    frame = frame.set_index("timestamp").sort_index()
    frame = frame[~frame.index.duplicated(keep="last")]

    for column in OHLCV_COLUMNS:
        frame[column] = pd.to_numeric(frame.get(column), errors="coerce")

    frame = frame.dropna(subset=["close"])
    if frame.empty:
        raise UpstreamError(source, "all candles were unusable")

    frame.attrs["source"] = source
    return frame[OHLCV_COLUMNS]
