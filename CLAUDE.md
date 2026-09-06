# Working in this repo

Vision is a crypto market terminal: a FastAPI backend that computes volatility
and risk statistics, and a React/Vite frontend that renders them as a 1980s
phosphor terminal.

## Run it

```bash
# backend (from backend/)
.venv/Scripts/python.exe -m uvicorn app.main:app --reload

# frontend (from frontend/)
npm run dev            # http://localhost:5173, proxies /api to :8000
```

The dev server binds `localhost`, which resolves to IPv6 on Windows —
`127.0.0.1:5173` is refused. Use `localhost`.

## Check it

```bash
cd backend  && .venv/Scripts/python.exe -m pytest   # 29 tests, no network
cd frontend && npm run typecheck && npm run build
```

Tests are offline by design: the analytics fixtures simulate geometric Brownian
motion with a known sigma, so the estimators are checked against a value we
control rather than against whatever the market did today.

## Conventions that matter

**Percentages are fractions everywhere** — `0.0241` is +2.41%. Adapters convert
at the boundary (Binance reports percent; `binance.py` divides by 100). Only
`lib/format.ts` multiplies by 100, and only for display.

**A statistic that cannot be computed is `null`, never a guess.** A window is
only reported when there are enough bars to fill it — a coin with ten days of
history reports no 90-day volatility. Do not relax this to avoid a dash in the
UI.

**NaN and infinity must never reach the JSON.** `summary._clean` converts them
to `None`; `test_payload_is_json_safe` asserts it with `allow_nan=False`.

**A year is 365 days**, not 252. Crypto trades continuously. See
`analytics/returns.py`.

**Components read colours from CSS tokens only.** No component hard-codes a hex
value, including the chart — it reads `--phosphor` and friends at mount so the
green/amber tube switch works. Tokens live in `frontend/src/styles/tokens.css`.

## Layout

- `backend/app/analytics/` — the actual product. Pure functions over frames;
  `summary.py` assembles the API payload.
- `backend/app/sources/` — one adapter per provider, each normalising to the
  same OHLCV frame.
- `backend/app/service.py` — cache, source fallback, and the merge of Binance
  prices with CoinGecko metadata. Routers stay thin; provider decisions live
  here.
- `backend/app/cache.py` — TTL cache with single-flight. Concurrent misses on
  one key collapse to a single upstream call.
- `frontend/src/api/types.ts` — mirrors the backend payload by hand. Change the
  Python schema and this file together.

## Data sources

Binance is primary for candles (`data-api.binance.vision` first — it is not
regionally blocked the way `api.binance.com` can be). CryptoCompare is the
fallback. CoinGecko supplies names, logos and market cap; if it is rate-limited
the market list still renders without them, which is deliberate.

No API key is required to run anything.

## Documentation

- [docs/STATISTICS.md](docs/STATISTICS.md) — what every metric means and how to
  read combinations of them. Update it when adding a statistic.
- [docs/DESIGN.md](docs/DESIGN.md) — the design system, breakpoints, and the
  layout traps already found and fixed.
