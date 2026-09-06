import asyncio

import pytest

from app.cache import TTLCache


@pytest.mark.asyncio
async def test_returns_cached_value_within_ttl():
    cache = TTLCache()
    calls = 0

    async def produce():
        nonlocal calls
        calls += 1
        return calls

    assert await cache.get_or_set("k", 60, produce) == 1
    assert await cache.get_or_set("k", 60, produce) == 1
    assert calls == 1


@pytest.mark.asyncio
async def test_expired_entry_is_recomputed():
    cache = TTLCache()
    calls = 0

    async def produce():
        nonlocal calls
        calls += 1
        return calls

    await cache.get_or_set("k", 0, produce)
    await asyncio.sleep(0.01)
    assert await cache.get_or_set("k", 0, produce) == 2


@pytest.mark.asyncio
async def test_single_flight_collapses_concurrent_misses():
    """Ten widgets asking at once must cost one upstream call, not ten."""
    cache = TTLCache()
    calls = 0

    async def produce():
        nonlocal calls
        calls += 1
        await asyncio.sleep(0.05)  # a slow upstream
        return "value"

    results = await asyncio.gather(*(cache.get_or_set("k", 60, produce) for _ in range(10)))
    assert results == ["value"] * 10
    assert calls == 1


@pytest.mark.asyncio
async def test_invalidate_by_prefix():
    cache = TTLCache()
    for key in ("ohlcv:BTC", "ohlcv:ETH", "markets"):
        await cache.get_or_set(key, 60, _const(key))

    assert cache.invalidate("ohlcv:") == 2
    assert cache.stats()["entries"] == 1


def _const(value):
    async def produce():
        return value

    return produce
