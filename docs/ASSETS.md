# Generating image assets

Image assets are produced through [polza.ai](https://polza.ai/dashboard), an
OpenRouter-style aggregator: one key, 21 image models, billed per image in
roubles. Nothing in the running app talks to it — this is a build-time tool
only, driven by [`scripts/generate_assets.py`](../scripts/generate_assets.py).

```bash
python scripts/generate_assets.py --list          # models and live prices
python scripts/generate_assets.py noise           # one asset
python scripts/generate_assets.py --all --model black-forest-labs/flux.2-pro
```

Output lands in `frontend/public/generated/`, which is git-ignored: the images
are reproducible from the prompts in the script, so the prompts are the source
of truth rather than the PNGs.

## How much the terminal actually needs

Very little, and that is deliberate. The CRT look — scanlines, vignette, glow,
corner brackets, meter hatching — is drawn in CSS, and the favicon is an inline
SVG. Generated art earns its place only where CSS cannot go: a social preview
image, a photographic hero, a noise texture with genuine high-frequency detail.

Resist adding a generated background behind the data. Every one of these models
produces something busier than a screen full of numbers can survive.

## The API

Base URL `https://api.polza.ai/api/v1`, bearer auth. Two relevant endpoints,
`/media` and an OpenAI-compatible `/images/generations`; the script uses
`/media` because its parameters are documented and validated per model.

`POST /media` is **synchronous** — the response carries the finished URL and the
cost:

```json
{
  "model": "tongyi-mai/z-image",
  "input": {
    "prompt": "…",
    "aspect_ratio": "1:1",
    "output_format": "png"
  }
}
```

```json
{
  "id": "gen_…", "status": "completed",
  "data": [{ "url": "https://s3.polza.ai/…png" }],
  "usage": { "cost_rub": 1.4 }
}
```

### Traps

- **Every generation parameter goes inside `input`.** Putting `aspect_ratio`
  next to `model` does not error — it is ignored, and the call is then rejected
  for the missing parameter, which reads as a server bug rather than a
  malformed request.
- **Required parameters vary by model** and are published per model in
  `GET /models` under `parameters`. `z-image` demands `aspect_ratio`; others
  do not.
- **Error messages are in Russian**, and they are specific and useful — read
  them rather than guessing.
- Prices in `GET /models` are RUB and come either as `per_request` or as
  `tiers` keyed by conditions such as `image_resolution=2K`.

## Choosing a model

| Need | Model | RUB/image |
| ---- | ----- | --------- |
| Textures, backgrounds, bulk | `tongyi-mai/z-image` | 1.4 |
| General purpose, good prompt adherence | `google/gemini-2.5-flash-image` | 2.9 |
| Anything containing legible text | `openai/gpt-image-1.5` | 3 (medium) |
| Highest detail | `black-forest-labs/flux.2-pro` | 5 (1K), 7 (2K) |

`--list` prints the current set; the catalogue changes.
