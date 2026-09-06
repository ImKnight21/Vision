"""Market data endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Path, Query

from app import service
from app.analytics.returns import INTERVAL_SECONDS
from app.sources.base import UpstreamError

router = APIRouter(prefix="/api", tags=["market"])

SYMBOL_PATTERN = r"^[A-Za-z0-9]{4,20}$"


@router.get("/intervals", summary="Candle intervals this API accepts")
async def list_intervals() -> dict:
    return {
        "intervals": [
            {"value": key, "seconds": seconds}
            for key, seconds in sorted(INTERVAL_SECONDS.items(), key=lambda kv: kv[1])
        ]
    }


@router.get("/markets", summary="Ranked overview of tradable pairs")
async def list_markets(
    limit: int = Query(100, ge=1, le=500, description="How many pairs to return"),
) -> dict:
    try:
        rows = await service.get_markets(limit)
    except UpstreamError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"count": len(rows), "markets": rows}


@router.get("/ohlcv/{symbol}", summary="Raw candles for one pair")
async def get_ohlcv(
    symbol: str = Path(..., pattern=SYMBOL_PATTERN, examples=["BTCUSDT"]),
    interval: str = Query("1d"),
    limit: int = Query(500, ge=10, le=1000),
) -> dict:
    frame = await _load(symbol, interval, limit)
    return {
        "symbol": symbol.upper(),
        "interval": interval,
        "source": frame.attrs.get("source", "unknown"),
        "candles": service.frame_to_candles(frame),
    }


@router.get("/stats/{symbol}", summary="Full statistical profile for one pair")
async def get_stats(
    symbol: str = Path(..., pattern=SYMBOL_PATTERN, examples=["BTCUSDT"]),
    interval: str = Query("1d"),
    limit: int = Query(500, ge=30, le=1000),
) -> dict:
    try:
        return await service.get_summary(symbol, interval, limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except UpstreamError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/overview/{symbol}", summary="Candles and statistics in one round trip")
async def get_overview(
    symbol: str = Path(..., pattern=SYMBOL_PATTERN, examples=["BTCUSDT"]),
    interval: str = Query("1d"),
    limit: int = Query(500, ge=30, le=1000),
) -> dict:
    """What the detail view needs. One request instead of two, and both halves
    are guaranteed to describe the same candles."""
    frame = await _load(symbol, interval, limit)
    from app.analytics import build_summary

    summary = build_summary(frame, interval, symbol.upper())
    summary["source"] = frame.attrs.get("source", "unknown")
    return {
        "symbol": symbol.upper(),
        "interval": interval,
        "source": summary["source"],
        "candles": service.frame_to_candles(frame),
        "stats": summary,
    }


async def _load(symbol: str, interval: str, limit: int):
    try:
        return await service.get_ohlcv(symbol, interval, limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except UpstreamError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
