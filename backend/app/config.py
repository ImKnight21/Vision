"""Runtime configuration, loaded from environment / .env at the repo root."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """App settings.

    The app's own knobs are read from ``VISION_*``; third-party credentials keep
    their conventional unprefixed names so they can be pasted in as-is.
    """

    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        env_prefix="VISION_",
        extra="ignore",
    )

    host: str = "127.0.0.1"
    port: int = 8000

    # Comma-separated in the environment, split into a list below.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Cache time-to-live in seconds, per data class.
    ttl_markets: int = 60
    ttl_ohlcv: int = 120
    ttl_meta: int = 3600

    # Outbound HTTP budget for a single upstream call.
    http_timeout: float = 15.0

    # Total budget for optional metadata enrichment. Exceeding it drops the
    # extra fields rather than delaying the response.
    meta_budget: float = 6.0

    coingecko_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("COINGECKO_API_KEY", "VISION_COINGECKO_API_KEY"),
    )
    cryptocompare_api_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "CRYPTOCOMPARE_API_KEY", "VISION_CRYPTOCOMPARE_API_KEY"
        ),
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
