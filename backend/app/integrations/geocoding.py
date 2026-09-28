from typing import Any
from urllib.parse import urlencode

import httpx

from app.integrations.cache import Cache


class GeocodingError(RuntimeError):
    pass


class NominatimClient:
    def __init__(self, base_url: str, user_agent: str, cache: Cache, ttl: int) -> None:
        self.base_url = base_url.rstrip("/")
        self.user_agent = user_agent
        self.cache = cache
        self.ttl = ttl

    async def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        normalized_query = query.strip()
        cache_key = f"geocode:{normalized_query.casefold()}:{limit}"
        cached = await self.cache.get_json(cache_key)
        if cached is not None:
            return list(cached)
        params = {
            "q": normalized_query,
            "format": "jsonv2",
            "limit": limit,
            "addressdetails": 1,
        }
        try:
            async with httpx.AsyncClient(
                headers={"User-Agent": self.user_agent}, timeout=15
            ) as client:
                response = await client.get(f"{self.base_url}/search?{urlencode(params)}")
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise GeocodingError("Geocoding provider is unavailable") from exc
        try:
            payload = response.json()
        except ValueError as exc:
            raise GeocodingError("Geocoding provider returned an invalid response") from exc
        if not isinstance(payload, list):
            raise GeocodingError("Geocoding provider returned an invalid response")

        results: list[dict[str, Any]] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            try:
                latitude = float(item["lat"])
                longitude = float(item["lon"])
                display_name = str(item["display_name"])
            except (KeyError, TypeError, ValueError):
                continue
            if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
                continue
            results.append(
                {
                    "display_name": display_name,
                    "latitude": latitude,
                    "longitude": longitude,
                    "type": item.get("type"),
                }
            )
        await self.cache.set_json(cache_key, results, self.ttl)
        return results
