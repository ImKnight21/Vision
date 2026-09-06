# Vision API

The backend half of [Vision](https://github.com/ImKnight21/Vision), a crypto
market terminal. FastAPI plus pandas: it fetches candles from Binance, falls
back to CryptoCompare, merges CoinGecko metadata, and computes volatility,
drawdown, tail-risk, regime, liquidity and relative-to-BTC statistics.

Interactive API docs are at `/docs`; `/api/health` is the liveness probe.

Deployed to Render from [render.yaml](../render.yaml); see
[docs/DEPLOY.md](../docs/DEPLOY.md). The [Dockerfile](Dockerfile) is not used by
that deployment and is kept for running the API anywhere else unchanged.

## Endpoints

| Endpoint | Purpose |
| -------- | ------- |
| `/api/health` | Liveness plus cache occupancy. |
| `/api/markets?limit=` | Ranked USDT pairs with price, volume and market cap. |
| `/api/ohlcv/{symbol}` | Raw candles. |
| `/api/stats/{symbol}` | The full statistical profile. |
| `/api/overview/{symbol}` | Candles and statistics in one round trip. |
| `/api/compare?symbols=` | Correlation matrix across 2 to 8 coins. |

## Configuration

Every setting is optional; no API key is needed. The one worth setting in
production is `VISION_CORS_ORIGINS`, a comma-separated list of the origins
allowed to call this API directly. It can be left alone when the frontend
reaches the API through a same-origin proxy.
