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
cd backend  && .venv/Scripts/python.exe -m pytest   # 89 tests, no network
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

**No user-visible string may change the layout when the language changes.**
Wrap text that varies between locales in `<Stable>` (`i18n/Stable.tsx`): it
renders every locale's variant into one grid cell and hides all but the active
one, so the box is as wide as the longest translation whichever is showing.
Hand-written `min-width` values are not acceptable here -- they have to be
re-measured by a person whenever a translation changes, and silently stop being
true when nobody does. Measured before this existed: switching to English moved
the header controls by up to 93px.

**On a phone the chart comes before the reference data.** `CoinHeader` and
`CoinFacts` are separate sections purely so `order` can put the chart between
them below 960px; on wider screens CSS pulls them flush so they read as one
panel. Do not merge them back together.

**Touch targets are keyed on `(pointer: coarse)`, not on viewport width.** A
touchscreen tablet is wide and still has no cursor. Standalone controls get
44px; the inline term triggers in `Hint` get 32px through an invisible
`::before`, because padding them to 44px would double the height of every
statistics panel and WCAG treats inline targets differently from buttons.

**Terminology is explained by `Hint`, never by a `title` attribute.** A native
tooltip cannot be opened by touch at all, so on a phone those explanations were
unreachable. `Hint` hovers on a mouse, taps open a sheet on a phone, and the
popup is portalled to `document.body` -- the panels sit inside `.app__main`,
which scrolls, and a positioned element inside a scrolling box is clipped at
its edge. Accessibility never depends on the popup: the text sits in the DOM
permanently behind `aria-describedby`, and the popup is `aria-hidden`.

**Em dashes are banned in user-visible text.** They are the clearest tell of
generated copy and they render inconsistently in a monospace column. Use a
period, a comma, a colon, or `--`. Code comments are exempt.

**The dev server caches CSS by content.** If a stylesheet's rules stop applying
after an overwrite, Vite is serving an empty module for it (check
`curl localhost:5173/src/.../X.css`); change the file's content to invalidate it.
Restarting and clearing `node_modules/.vite` does not help.

## Data sources

Candles and tickers come from a chain declared in `service.py`, tried in order:

1. **Binance** (`data-api.binance.vision` first — it is not regionally blocked
   the way `api.binance.com` can be). Primary, and the figures users expect to
   match.
2. **Bybit.** Keyless, and its spot symbols are `BTCUSDT` exactly like
   Binance's, so it substitutes without a translation table. Prices come from a
   different book, so they will not agree tick for tick; over a statistical
   window that is immaterial.
3. **CryptoCompare.** Last, because it now answers `401` without an API key.

Binance answers **`418`** once an IP exceeds its request weight, and shared
hosting egresses through addresses other tenants are also hammering — so on a
free host the ban is the normal case, not an exotic one. That is what Bybit is
insurance against. Before Bybit existed the chain fell to CryptoCompare, which
`401`s, and the whole site returned 502.

CoinGecko supplies names, logos and market cap. Its free tier rate-limits a
shared hosting IP hard: measured 3 successes in 8 attempts from Render, the
refusals arriving in under a second rather than exhausting the budget. So the
metadata has **its own hour-long cache entry**, separate from the two-minute
market list. Tying the two together threw away every success within minutes and
showed as a table with no logos. A refusal is never cached, or one 429 would
blank the names for an hour. If it is still unavailable the market list renders
without those fields, which is deliberate.

`/api/latest/{symbol}` serves the forming bar alone, cached for `ttl_live`
(5 seconds). It is polled by every open chart, so it deliberately carries no
statistics. It is a separate cache entry from `/api/ohlcv`, which caches for
minutes because settled history does not change; one entry for both would force
a choice between a stale chart and refetching hundreds of bars every few
seconds. The client stops polling while the tab is hidden.

**Leveraged tokens are excluded, but the suffix alone is not evidence.** JUP
(Jupiter, ~$18M daily) and SYRUP both end in `UP`, and BEAR and BULL are coins
named exactly after the suffixes. `sources/base.is_leveraged` strips the suffix
and drops the row only when what remains is itself a traded base: `BTCUP`
leaves `BTC` and is a wrapper, `JUP` leaves `J` and is a coin.

No API key is required to run anything: Binance and Bybit are both keyless.
`COINGECKO_API_KEY` and `CRYPTOCOMPARE_API_KEY` only widen what already works.

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
