from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://geomarket:geomarket@localhost:5432/geomarket"
    redis_url: str = "redis://localhost:6379/0"
    overpass_url: str = "https://overpass-api.de/api/interpreter"
    overpass_fallback_urls: tuple[str, ...] = (
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    )
    nominatim_url: str = "https://nominatim.openstreetmap.org"
    http_user_agent: str = "GeoMarketAI/0.1 (development)"
    cache_ttl_seconds: int = Field(default=3600, ge=60, le=86400)
    cors_origins: list[str] = ["http://localhost:5173"]
    cors_origin_regex: str | None = r"^http://(localhost|127\.0\.0\.1)(:\d+)?$"
    radii_m: tuple[int, ...] = (250, 500, 1000)
    max_candidates: int = 400
    request_timeout_seconds: float = 15.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
