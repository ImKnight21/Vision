#!/usr/bin/env python
"""Generate image assets through polza.ai.

polza.ai is an OpenRouter-style aggregator: one key, many providers. Its
``/api/v1/media`` endpoint is synchronous — the response carries the finished
image URL and what the call cost in roubles.

    python scripts/generate_assets.py --list
    python scripts/generate_assets.py noise
    python scripts/generate_assets.py --all --model black-forest-labs/flux.2-pro

Needs POLZA_API_KEY in the repo's .env (see .env.example).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "frontend" / "public" / "generated"

DEFAULT_BASE_URL = "https://api.polza.ai/api/v1"

# Cheap and good enough for texture work. Override with --model; every image
# model on the platform accepts the same request shape.
DEFAULT_MODEL = "tongyi-mai/z-image"

# Prompts are deliberately explicit about "no text": every one of these models
# will happily render garbled lettering into an abstract texture otherwise.
ASSETS: dict[str, dict[str, str]] = {
    "noise": {
        "prompt": (
            "Seamless tileable CRT phosphor screen grain texture, near-black "
            "background, very faint green speckle noise, subtle horizontal "
            "scanlines, high frequency detail, abstract, no text, no objects, "
            "no logo, flat, evenly lit"
        ),
        "aspect_ratio": "1:1",
    },
    "og": {
        "prompt": (
            "Dark moody product shot of a 1980s CRT financial trading terminal "
            "glowing green in a dim room, candlestick chart on the screen, "
            "phosphor glow, scanlines, shallow depth of field, cinematic, "
            "photographic, no readable text, no logo"
        ),
        "aspect_ratio": "16:9",
    },
    "grid": {
        "prompt": (
            "Seamless tileable dark technical grid pattern, thin faint green "
            "hairlines on near-black, graph paper, perfectly straight lines, "
            "abstract, no text, no objects"
        ),
        "aspect_ratio": "1:1",
    },
}


def load_env(path: Path) -> None:
    """Minimal .env reader — avoids a dependency for one file of KEY=VALUE."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def post(url: str, payload: dict, api_key: str, timeout: float) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def generate(name: str, spec: dict, model: str, base_url: str, api_key: str,
             timeout: float) -> Path:
    print(f"  {name:<8} generating via {model} …", flush=True)

    body = {
        "model": model,
        # Every documented knob lives under `input`, not at the top level —
        # passing aspect_ratio beside `model` is silently ignored and the API
        # then rejects the call for the missing parameter.
        "input": {
            "prompt": spec["prompt"],
            "aspect_ratio": spec["aspect_ratio"],
            "output_format": "png",
        },
    }

    result = post(f"{base_url}/media", body, api_key, timeout)

    if result.get("status") not in {"completed", None}:
        raise RuntimeError(f"{name}: unexpected status {result.get('status')!r}")

    entries = result.get("data") or []
    if not entries or not entries[0].get("url"):
        raise RuntimeError(f"{name}: response carried no image URL")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    destination = OUTPUT_DIR / f"{name}.png"
    with urllib.request.urlopen(entries[0]["url"], timeout=timeout) as source:
        destination.write_bytes(source.read())

    cost = (result.get("usage") or {}).get("cost_rub")
    size_kb = destination.stat().st_size / 1024
    print(f"  {name:<8} -> {destination.relative_to(REPO_ROOT)} "
          f"({size_kb:.0f} kB, {cost} RUB)")
    return destination


def list_models(base_url: str, api_key: str, timeout: float) -> None:
    request = urllib.request.Request(
        f"{base_url}/models", headers={"Authorization": f"Bearer {api_key}"}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        models = json.loads(response.read().decode("utf-8"))["data"]

    image_models = [m for m in models if m.get("type") == "image"]
    print(f"{len(image_models)} image models available\n")
    print(f"{'MODEL':<44}COST (RUB)")
    print("-" * 66)
    for model in sorted(image_models, key=lambda m: m["id"]):
        pricing = (model.get("top_provider") or {}).get("pricing") or {}
        if pricing.get("tiers"):
            cost = ", ".join(
                f"{','.join(t.get('conditions') or ['base'])}={float(t['cost_rub']):g}"
                for t in pricing["tiers"]
            )
        elif pricing.get("per_request"):
            cost = f"{float(pricing['per_request']):g} per image"
        else:
            cost = "see dashboard"
        print(f"{model['id']:<44}{cost[:60]}")


def main() -> int:
    load_env(REPO_ROOT / ".env")

    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("assets", nargs="*", choices=[*ASSETS, []],
                        help="which assets to generate")
    parser.add_argument("--all", action="store_true", help="generate every asset")
    parser.add_argument("--list", action="store_true",
                        help="list the image models this key can reach, with prices")
    parser.add_argument("--model", default=os.environ.get("POLZA_IMAGE_MODEL") or DEFAULT_MODEL)
    parser.add_argument("--timeout", type=float, default=240.0)
    args = parser.parse_args()

    api_key = os.environ.get("POLZA_API_KEY", "").strip()
    if not api_key:
        print("POLZA_API_KEY is not set. Copy .env.example to .env and fill it in.",
              file=sys.stderr)
        return 2

    base_url = (os.environ.get("POLZA_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")

    if args.list:
        list_models(base_url, api_key, args.timeout)
        return 0

    wanted = list(ASSETS) if args.all else args.assets
    if not wanted:
        parser.print_help()
        return 2

    print(f"model: {args.model}\noutput: {OUTPUT_DIR.relative_to(REPO_ROOT)}\n")
    failures = 0
    for name in wanted:
        try:
            generate(name, ASSETS[name], args.model, base_url, api_key, args.timeout)
        except Exception as exc:  # noqa: BLE001 — report and continue
            print(f"  {name:<8} FAILED: {exc}", file=sys.stderr)
            failures += 1

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
