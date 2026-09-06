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
cd backend  && .venv/Scripts/python.exe -m pytest   # 62 tests, no network
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

**New text colours must be measured, not eyeballed.** Every text token clears
WCAG AA against its background *with the scanline overlay applied*. Use
`--rule` / `--rule-faint` for decorative lines; never put text in them. The
method and the numbers are in `docs/DESIGN.md`.

**Theme attributes are written synchronously in the toggle handler**, not left
to an effect: React runs a child's effects before its parent's, so the chart
would otherwise re-read the previous theme's palette. See
`hooks/useDisplay.ts`.

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
- `frontend/src/i18n/dictionary.ts` — every UI string, English and Russian.
  English is the source of truth and Russian is typed as a record over its keys,
  so a missing translation is a compile error. **No user-visible string belongs
  anywhere else.**

**Em dashes are banned in user-visible text.** They are the clearest tell of
generated copy and they render inconsistently in a monospace column. Use a
period, a comma, a colon, or `--`. Code comments are exempt.

**The dev server caches CSS by content.** If a stylesheet's rules stop applying
after an overwrite, Vite is serving an empty module for it (check
`curl localhost:5173/src/.../X.css`); change the file's content to invalidate it.
Restarting and clearing `node_modules/.vite` does not help.

## Data sources

Binance is primary for candles (`data-api.binance.vision` first — it is not
regionally blocked the way `api.binance.com` can be). CryptoCompare is the
fallback. CoinGecko supplies names, logos and market cap; if it is rate-limited
the market list still renders without them, which is deliberate.

No API key is required to run anything.

## Deployment

Frontend on Netlify, backend on Render, with `netlify.toml` proxying `/api/*`
to the Render service so the browser stays same-origin and CORS never applies.
Both sides are declared in `netlify.toml` and `render.yaml`; the walkthrough is
[docs/DEPLOY.md](docs/DEPLOY.md).

Two things that are easy to get wrong:

- **The backend region must not be in the US.** Binance answers 451 to US IPs,
  which silently demotes every request to the CryptoCompare fallback rather
  than failing visibly. `render.yaml` pins Frankfurt.
- **`netlify.toml` hard-codes the Render host.** There is no env-var
  substitution in Netlify redirects, so that line is edited by hand when the
  service URL changes.

`npm run preview` serves the real build with the same proxy, which is the
closest local mirror of the deployed site.

## Documentation

- [docs/STATISTICS.md](docs/STATISTICS.md) — what every metric means and how to
  read combinations of them. Update it when adding a statistic.
- [docs/DESIGN.md](docs/DESIGN.md) — the design system, breakpoints, and the
  layout traps already found and fixed.
