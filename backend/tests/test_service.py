import asyncio

import pytest

from app import service
from app.cache import cache
from app.sources import binance, bybit, coingecko
from app.sources.base import UpstreamError

TICKERS = [
    {
        "symbol": "BTCUSDT", "base": "BTC", "quote": "USDT", "price": 70000.0,
        "change_24h": 0.01, "high_24h": 71000.0, "low_24h": 69000.0,
        "volume_24h": 1e9, "trades_24h": 100, "source": "binance",
    },
    {
        "symbol": "ETHUSDT", "base": "ETH", "quote": "USDT", "price": 2500.0,
        "change_24h": -0.02, "high_24h": 2600.0, "low_24h": 2400.0,
        "volume_24h": 5e8, "trades_24h": 80, "source": "binance",
    },
]

META = [
    {
        "id": "bitcoin", "base": "BTC", "name": "Bitcoin", "image": "http://x/btc.png",
        "market_cap": 1.4e12, "market_cap_rank": 1, "change_7d": 0.05,
        "change_30d": 0.1, "circulating_supply": 19e6, "max_supply": 21e6,
        "ath": 100000.0, "ath_change": -0.3, "source": "coingecko",
    },
]


@pytest.fixture(autouse=True)
def clear_cache():
    """The cache is a process-wide singleton; tests must not see each other."""
    cache.invalidate()
    yield
    cache.invalidate()


@pytest.fixture
def stub_tickers(monkeypatch):
    async def fake():
        return list(TICKERS)

    monkeypatch.setattr(binance, "fetch_tickers", fake)


@pytest.mark.asyncio
async def test_merges_prices_with_metadata(monkeypatch, stub_tickers):
    async def fake_markets(per_page=250, page=1):
        return list(META)

    monkeypatch.setattr(coingecko, "fetch_markets", fake_markets)

    rows = await service.get_markets(10)
    btc = next(r for r in rows if r["symbol"] == "BTCUSDT")

    assert btc["name"] == "Bitcoin"
    assert btc["market_cap_rank"] == 1
    assert btc["price"] == 70000.0  # price always comes from the exchange


@pytest.mark.asyncio
async def test_slow_metadata_does_not_delay_the_list(monkeypatch, stub_tickers):
    """CoinGecko is enrichment. If it stalls, the prices still ship."""

    async def hanging(per_page=250, page=1):
        await asyncio.sleep(30)
        return list(META)

    monkeypatch.setattr(coingecko, "fetch_markets", hanging)
    monkeypatch.setattr(service.get_settings(), "meta_budget", 0.05)

    rows = await asyncio.wait_for(service.get_markets(10), timeout=5)

    assert [r["symbol"] for r in rows] == ["BTCUSDT", "ETHUSDT"]
    # Enrichment fields degrade to None rather than the request failing.
    assert all(r["market_cap"] is None for r in rows)
    assert rows[0]["name"] == "BTC"  # falls back to the ticker's base asset


@pytest.mark.asyncio
async def test_failing_metadata_does_not_fail_the_list(monkeypatch, stub_tickers):
    async def boom(per_page=250, page=1):
        raise UpstreamError("coingecko", "HTTP 429", status=429)

    monkeypatch.setattr(coingecko, "fetch_markets", boom)

    rows = await service.get_markets(10)
    assert len(rows) == 2


@pytest.mark.asyncio
async def test_failing_prices_do_fail_the_list(monkeypatch):
    """Without an exchange there is nothing to show, so this one propagates."""

    async def boom():
        raise UpstreamError("binance", "all hosts failed")

    # Every ticker source has to be stubbed, or the fallback chain reaches the
    # network and the test stops being offline.
    monkeypatch.setattr(binance, "fetch_tickers", boom)
    monkeypatch.setattr(bybit, "fetch_tickers", boom)

    async def fake_markets(per_page=250, page=1):
        return list(META)

    monkeypatch.setattr(coingecko, "fetch_markets", fake_markets)

    with pytest.raises(UpstreamError):
        await service.get_markets(10)


@pytest.mark.asyncio
async def test_ranked_coins_sort_before_unranked(monkeypatch, stub_tickers):
    async def fake_markets(per_page=250, page=1):
        return list(META)

    monkeypatch.setattr(coingecko, "fetch_markets", fake_markets)

    rows = await service.get_markets(10)
    assert rows[0]["symbol"] == "BTCUSDT"  # rank 1
    assert rows[1]["market_cap_rank"] is None  # ETH has no metadata row here


@pytest.mark.asyncio
async def test_rejects_unknown_interval():
    with pytest.raises(ValueError):
        await service.get_ohlcv("BTCUSDT", "1y", 100)
