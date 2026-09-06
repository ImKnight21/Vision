"""Vision API — crypto market statistics.

Run locally:  uvicorn app.main:app --reload  (from the backend/ directory)
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.cache import cache
from app.config import get_settings
from app.routers import market
from app.sources.base import close_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    # The pooled httpx client outlives individual requests, so it is closed here
    # rather than per-call.
    await close_client()


app = FastAPI(
    title="Vision API",
    description="Volatility and risk statistics for crypto markets.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(market.router)


@app.get("/api/health", tags=["meta"])
async def health() -> dict:
    return {"status": "ok", "version": app.version, "cache": cache.stats()}
