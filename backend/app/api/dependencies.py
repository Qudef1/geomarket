from functools import lru_cache
from typing import cast

from redis.asyncio import Redis

from app.core.config import get_settings
from app.integrations.cache import RedisCache
from app.integrations.geocoding import NominatimClient
from app.integrations.overpass import OverpassClient
from app.services.analysis import AnalysisService


@lru_cache
def get_redis() -> Redis:
    return cast(Redis, Redis.from_url(get_settings().redis_url, decode_responses=True))


def get_analysis_service() -> AnalysisService:
    settings = get_settings()
    cache = RedisCache(get_redis())
    client = OverpassClient(
        settings.overpass_url,
        settings.http_user_agent,
        cache,
        settings.cache_ttl_seconds,
        settings.overpass_fallback_urls,
    )
    return AnalysisService(client)


def get_geocoder() -> NominatimClient:
    settings = get_settings()
    return NominatimClient(
        settings.nominatim_url,
        settings.http_user_agent,
        RedisCache(get_redis()),
        settings.cache_ttl_seconds,
    )
