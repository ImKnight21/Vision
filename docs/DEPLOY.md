# Deployment

Vision ships as two halves that are hosted separately:

| Half | Host | Why |
| ---- | ---- | --- |
| `frontend/` | Netlify | Static build; Netlify serves it from a CDN. |
| `backend/` | Render | Netlify Functions run JavaScript and Go. The API is Python with pandas, so it needs a Python host. |

Netlify proxies `/api/*` through to Render, so the browser only ever talks to
one origin. That is the reason there is no CORS configuration to get wrong.

Deploy the backend **first**: the frontend's proxy needs its URL.

---

## 1. Backend on Render

Render reads [`render.yaml`](../render.yaml) and creates the service from it.

1. In the Render dashboard: **New > Blueprint**, and select this repository.
2. Render shows the service it found (`vision-api`, free plan, Frankfurt).
   Apply it.
3. Wait for the first build. Installing pandas and numpy takes a few minutes.
4. Copy the service URL from the top of the service page. It looks like
   `https://vision-api.onrender.com`, **but Render appends a suffix when the
   plain name is already taken globally**, so copy the real one rather than
   assuming.

Check it before moving on:

```bash
curl https://YOUR-SERVICE.onrender.com/api/health
# {"status":"ok","version":"0.1.0","cache":{"entries":0,"live":0}}

curl "https://YOUR-SERVICE.onrender.com/api/stats/BTCUSDT?interval=1d&limit=200" | head -c 200
```

The second call is the one that matters: it proves the host can actually reach
Binance.

### Why Frankfurt

Binance answers `451` to US IP addresses. A US region would leave the primary
candle source unreachable and quietly demote every request to the
CryptoCompare fallback, which aggregates across exchanges and will not match
Binance tick for tick. Singapore works too. `render.yaml` pins Frankfurt.

If `/api/stats/BTCUSDT` returns data with `"source":"cryptocompare"`, Binance is
being blocked from that region and the fallback is carrying the app.

---

## 2. Point the frontend at it

Edit one line in [`netlify.toml`](../netlify.toml):

```toml
[[redirects]]
  from = "/api/*"
  to = "https://YOUR-SERVICE.onrender.com/api/:splat"   # <- this host
  status = 200
  force = true
```

`status = 200` makes it a proxy rather than a redirect: Netlify fetches the
backend server-side and returns the response as its own, so the browser sees
everything on one origin. Commit and push.

---

## 3. Frontend on Netlify

The site already exists as `dreamy-cobbler-61f5ac`. Link the repository to it
rather than creating a second site:

1. **Site configuration > Build & deploy > Continuous deployment > Link
   repository**, and pick `ImKnight21/Vision`.
2. Leave every build setting alone. `netlify.toml` already declares the base
   directory, the build command, the publish directory and the Node version,
   and it overrides anything set in the UI.
3. Deploy.

From then on every push to `main` rebuilds the site.

Afterwards, check that the proxy is live:

```bash
curl -s https://dreamy-cobbler-61f5ac.netlify.app/api/health
```

That request never touches Render directly; if it answers, the proxy works.

---

## The free tier sleeps

Render's free instance spins down after 15 minutes without traffic, and the
next request spends roughly 50 seconds waking it. This is the single most
visible property of the deployment.

The interface handles it honestly: any request still outstanding after four
seconds raises a banner saying the backend is waking and roughly how long it
takes, so a cold start does not read as a hang. Loads after that are instant,
and `render.yaml` lengthens the cache lifetimes so the second visitor gets
cached data.

Ways to avoid it, in order of how much they cost:

- **Accept it.** For an informational terminal a slow first load is survivable,
  and the banner explains it.
- **Ping it on a schedule.** A cron job hitting `/api/health` every 10 minutes
  keeps the instance awake. Note that Render's free tier also caps monthly
  instance hours, so a permanent ping can exhaust them.
- **Pay for the starter plan.** No sleep, no cold start.

---

## Configuration

Nothing is required. The backend runs with no environment variables at all.
What `render.yaml` does set:

| Variable | Purpose |
| -------- | ------- |
| `PYTHON_VERSION` | Pins 3.11. |
| `VISION_CORS_ORIGINS` | Only consulted when a browser calls the API directly. Through the Netlify proxy the request is same-origin and no CORS check happens. |
| `VISION_TTL_MARKETS`, `VISION_TTL_OHLCV` | Longer cache lifetimes than the local defaults, because a cold start is expensive. |

`COINGECKO_API_KEY` is worth adding in the Render dashboard if the market list
often arrives without logos and market caps: that means CoinGecko is
rate-limiting the shared free-tier IP. The app degrades to prices alone rather
than failing, so it is a quality upgrade, not a fix.

Frontend variables live in `frontend/.env`, not the repo root, because that is
where Vite looks. See [`frontend/.env.example`](../frontend/.env.example). In
production `VITE_API_BASE_URL` stays unset so the app calls its own origin and
the proxy takes over.

---

## Alternatives

The [Dockerfile](../backend/Dockerfile) runs the API unchanged on any container
host: Fly, Koyeb, a Hugging Face Docker Space, or your own machine. It honours
`$PORT` and defaults to 7860. Render's deployment does not use it.

```bash
docker build -t vision-api backend
docker run -p 8000:8000 -e PORT=8000 vision-api
```

---

## Troubleshooting

**The site loads but every panel is empty, and the header says NO LINK.**
The proxy target is wrong. `curl https://YOUR-SITE.netlify.app/api/health`; a
404 from Netlify means the `to =` host in `netlify.toml` does not match the
Render URL.

**Everything is slow on the first visit, then fine.** That is the free instance
waking. Expected; see above.

**Prices appear but names, logos and market caps do not.** CoinGecko is being
rate-limited. Deliberate behaviour: the market list ships with exchange data
rather than waiting. Add `COINGECKO_API_KEY` to raise the limit.

**`"source":"cryptocompare"` on every response.** Binance is unreachable from
the backend's region. Check the region is not a US one.

**The Netlify build fails on `npm run build`.** Check the build log for the Node
version; `netlify.toml` pins 22, and a UI setting cannot override the file.
