"""Adapter parsing and the source fallback chain.

Every test here is offline: the point is that we read each provider's payload
correctly and switch providers when one refuses, not that the providers are up.
"""

import pandas as pd
import pytest

from app import service
from app.cache import cache
from app.sources import binance, bybit, cryptocompare
from app.sources.base import UpstreamError, is_leveraged

# Bybit returns candles newest-first: [startTime, o, h, l, c, volume, turnover].
BYBIT_KLINES = {
    "retCode": 0,
    "retMsg": "OK",
    "result": {
        "category": "spot",
        "symbol": "BTCUSDT",
        "list": [
            ["1788652800000", "79829.2", "80112.4", "79211.7", "79961.3", "2639.0", "2.1e8"],
            ["1788566400000", "79657.5", "80204.4", "79444.5", "79829.2", "3775.0", "3.0e8"],
            ["1788480000000", "81264.6", "81433.2", "78643.8", "79657.5", "8035.8", "6.4e8"],
        ],
    },
}

BYBIT_TICKERS = {
    "retCode": 0,
    "retMsg": "OK",
    "result": {
        "list": [
            {
                "symbol": "BTCUSDT", "lastPrice": "79961.3", "price24hPcnt": "0.0262",
                "highPrice24h": "80112.4", "lowPrice24h": "79211.7",
                "volume24h": "2639.0", "turnover24h": "210690250.0",
            },
            {
                "symbol": "ETHUSDT", "lastPrice": "2500.0", "price24hPcnt": "-0.0150",
                "highPrice24h": "2600.0", "lowPrice24h": "2400.0",
                "volume24h": "1000.0", "turnover24h": "2500000.0",
            },
            # Filtered: not a USDT pair.
            {
                "symbol": "XRPBTC", "lastPrice": "0.00001779", "price24hPcnt": "0.0023",
                "highPrice24h": "0.00001789", "lowPrice24h": "0.0000176",
                "volume24h": "166460.0", "turnover24h": "2.95",
            },
            # Filtered: leveraged wrapper, because "BTC" is itself listed.
            {
                "symbol": "BTC3LUSDT", "lastPrice": "1.0", "price24hPcnt": "0.08",
                "highPrice24h": "1.1", "lowPrice24h": "0.9",
                "volume24h": "10.0", "turnover24h": "10.0",
            },
            # Kept: ends in "UP" but "J" trades nowhere, so it is a real coin.
            {
                "symbol": "JUPUSDT", "lastPrice": "0.2644", "price24hPcnt": "0.011",
                "highPrice24h": "0.27", "lowPrice24h": "0.26",
                "volume24h": "1000.0", "turnover24h": "17934711.0",
            },
        ]
    },
}


@pytest.fixture(autouse=True)
def clear_cache():
    cache.invalidate()
    yield
    cache.invalidate()


def stub_bybit(monkeypatch, payload):
    async def fake(provider, url, *, params=None, headers=None, attempts=3):
        return payload

    monkeypatch.setattr(bybit, "fetch_json", fake)


# --------------------------------------------------------------------------
#  Bybit adapter
# --------------------------------------------------------------------------


async def test_bybit_candles_come_back_oldest_first(monkeypatch):
    stub_bybit(monkeypatch, BYBIT_KLINES)

    frame = await bybit.fetch_ohlcv("BTCUSDT", "1d", 3)

    assert list(frame.columns) == ["open", "high", "low", "close", "volume"]
    assert frame.index.is_monotonic_increasing
    # Bybit listed this row last; sorted, it is the first bar.
    assert frame["open"].iloc[0] == pytest.approx(81264.6)
    assert frame["close"].iloc[-1] == pytest.approx(79961.3)
    assert frame.attrs["source"] == "bybit"


async def test_bybit_reports_an_envelope_error_rather_than_no_candles(monkeypatch):
    """Bybit answers HTTP 200 on failure, so retCode is the real status."""
    stub_bybit(monkeypatch, {"retCode": 10001, "retMsg": "params error", "result": {}})

    with pytest.raises(UpstreamError, match="10001"):
        await bybit.fetch_ohlcv("NOPEUSDT", "1d", 10)


async def test_bybit_rejects_an_interval_it_cannot_serve(monkeypatch):
    stub_bybit(monkeypatch, BYBIT_KLINES)

    with pytest.raises(UpstreamError, match="unsupported interval"):
        await bybit.fetch_ohlcv("BTCUSDT", "3d", 10)


async def test_bybit_change_is_already_a_fraction(monkeypatch):
    """Binance reports percent and is divided by 100; Bybit must not be.

    Dividing here would report every move as a hundredth of itself, which looks
    plausible on screen and is the reason this has its own test.
    """
    stub_bybit(monkeypatch, BYBIT_TICKERS)

    rows = await bybit.fetch_tickers()
    btc = next(r for r in rows if r["symbol"] == "BTCUSDT")

    assert btc["change_24h"] == pytest.approx(0.0262)


async def test_bybit_tickers_use_quote_volume_and_drop_noise(monkeypatch):
    stub_bybit(monkeypatch, BYBIT_TICKERS)

    rows = await bybit.fetch_tickers()

    assert [r["symbol"] for r in rows] == ["BTCUSDT", "JUPUSDT", "ETHUSDT"]
    btc = rows[0]
    # turnover24h (quote), not volume24h (base) — the latter is not comparable
    # with Binance's figure and would rank the table wrongly.
    assert btc["volume_24h"] == pytest.approx(210690250.0)
    assert btc["trades_24h"] is None
    assert btc["base"] == "BTC" and btc["quote"] == "USDT"


# --------------------------------------------------------------------------
#  Fallback chain
# --------------------------------------------------------------------------


def frame_from(source: str) -> pd.DataFrame:
    index = pd.date_range("2024-01-01", periods=3, freq="D", tz="UTC")
    frame = pd.DataFrame(
        {"open": [1.0, 2, 3], "high": [2.0, 3, 4], "low": [0.5, 1, 2],
         "close": [1.5, 2.5, 3.5], "volume": [10.0, 11, 12]},
        index=index,
    )
    frame.attrs["source"] = source
    return frame


async def test_candles_fall_through_to_bybit_when_binance_is_banned(monkeypatch):
    """Binance answers 418 once an IP exceeds its weight. Shared hosting shares
    that IP, so this is the normal case there, not an exotic one."""

    async def banned(symbol, interval, limit=500):
        raise UpstreamError("binance", "all hosts failed: binance: HTTP 418")

    async def ok(symbol, interval, limit=500):
        return frame_from("bybit")

    monkeypatch.setattr(binance, "fetch_ohlcv", banned)
    monkeypatch.setattr(bybit, "fetch_ohlcv", ok)

    frame = await service.get_ohlcv("BTCUSDT", "1d", 3)
    assert frame.attrs["source"] == "bybit"


async def test_market_list_falls_through_to_bybit(monkeypatch):
    async def banned():
        raise UpstreamError("binance", "HTTP 418")

    async def ok():
        return [
            {"symbol": "BTCUSDT", "base": "BTC", "quote": "USDT", "price": 79961.3,
             "change_24h": 0.0262, "high_24h": 80112.4, "low_24h": 79211.7,
             "volume_24h": 2.1e8, "trades_24h": None, "source": "bybit"}
        ]

    async def no_meta(per_page=250, page=1):
        raise UpstreamError("coingecko", "HTTP 429")

    monkeypatch.setattr(binance, "fetch_tickers", banned)
    monkeypatch.setattr(bybit, "fetch_tickers", ok)
    monkeypatch.setattr(service.coingecko, "fetch_markets", no_meta)

    rows = await service.get_markets(10)

    assert len(rows) == 1
    assert rows[0]["source"] == "bybit"
    # No CoinGecko, so the name degrades to the ticker rather than going blank.
    assert rows[0]["name"] == "BTC"


async def test_every_source_failing_names_all_of_them(monkeypatch):
    """The error has to say what each provider said: with three sources, one
    provider's message alone is not enough to act on."""

    for module, provider in ((binance, "binance"), (bybit, "bybit"),
                             (cryptocompare, "cryptocompare")):
        async def fail(symbol, interval, limit=500, _p=provider):
            raise UpstreamError(_p, "HTTP 418" if _p == "binance" else "HTTP 401")

        monkeypatch.setattr(module, "fetch_ohlcv", fail)

    with pytest.raises(UpstreamError) as caught:
        await service.get_ohlcv("BTCUSDT", "1d", 3)

    message = str(caught.value)
    assert "binance" in message and "bybit" in message and "cryptocompare" in message


# --------------------------------------------------------------------------
#  Leveraged-token filter
# --------------------------------------------------------------------------


BASES = {"BTC", "ETH", "ADA", "JUP", "SYRUP", "BEAR", "BULL", "S", "1INCH"}


@pytest.mark.parametrize(
    "base",
    ["BTCUP", "BTCDOWN", "ETHBULL", "ETHBEAR", "ADAUP", "1INCHUP", "BTC3L", "ETH5S"],
)
def test_leveraged_wrappers_are_dropped(base):
    assert is_leveraged(base, BASES)


@pytest.mark.parametrize("base", ["JUP", "SYRUP", "BEAR", "BULL", "BTC", "1INCH"])
def test_real_coins_survive_the_filter(base):
    """The suffix alone is not evidence.

    JUP (Jupiter) and SYRUP both end in "UP" and are ordinary coins; JUP trades
    around $18M a day, so a bare suffix test drops one of the larger markets on
    the exchange without saying so. BEAR and BULL are coins named exactly after
    the suffixes. Stripping the suffix leaves "J", "SYR" and "", none of which
    trade, which is what separates them from a wrapper.
    """
    assert not is_leveraged(base, BASES)


# --------------------------------------------------------------------------
#  The live bar
# --------------------------------------------------------------------------


async def test_latest_returns_the_newest_bars_only(monkeypatch):
    calls = []

    async def fetch(symbol, interval, limit=500):
        calls.append(limit)
        return frame_from("binance")

    monkeypatch.setattr(binance, "fetch_ohlcv", fetch)

    payload = await service.get_latest("BTCUSDT", "1d")

    assert payload["symbol"] == "BTCUSDT"
    assert payload["source"] == "binance"
    # Two bars, so a boundary crossed between polls still yields the bar that
    # just closed rather than skipping it.
    assert calls == [2]
    assert payload["candles"][-1]["close"] == 3.5


async def test_live_and_history_do_not_share_a_cache_entry(monkeypatch):
    """The forming bar expires in seconds; the settled history does not.

    One entry for both would force a choice between a stale chart and
    refetching every bar on every poll, so this asserts they stay separate.
    """
    seen = []

    async def fetch(symbol, interval, limit=500):
        seen.append(limit)
        return frame_from("binance")

    monkeypatch.setattr(binance, "fetch_ohlcv", fetch)

    await service.get_ohlcv("BTCUSDT", "1d", 500)
    await service.get_latest("BTCUSDT", "1d")
    # A second poll is served from the live entry, not from the history one.
    await service.get_latest("BTCUSDT", "1d")

    assert seen == [500, 2]


async def test_latest_rejects_an_unknown_interval():
    with pytest.raises(ValueError, match="unsupported interval"):
        await service.get_latest("BTCUSDT", "7y")
