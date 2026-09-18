import hashlib
from typing import Any

import httpx

from app.configuration import POI_TAGS
from app.domain.models import POI, BoundingBox, Location, POICategory
from app.integrations.cache import Cache


class OverpassError(RuntimeError):
    pass


def _selectors(area: str) -> str:
    lines: list[str] = []
    for tags in POI_TAGS.values():
        for key, value in tags:
            selector = f'["{key}"]' if value == "*" else f'["{key}"="{value}"]'
            lines.append(f"nwr{selector}{area};")
    return "".join(lines)


def _category(tags: dict[str, str]) -> POICategory | None:
    for category, selectors in POI_TAGS.items():
        for key, value in selectors:
            if key in tags and (value == "*" or tags[key] == value):
                return category
    return None


class OverpassClient:
    def __init__(self, url: str, user_agent: str, cache: Cache, ttl: int) -> None:
        self.url, self.user_agent, self.cache, self.ttl = url, user_agent, cache, ttl

    async def around(self, location: Location, radius_m: int = 1000) -> list[POI]:
        area = f"(around:{radius_m},{location.latitude},{location.longitude})"
        return await self._fetch(f"[out:json][timeout:25];({_selectors(area)});out center tags;")

    async def in_bounds(self, bounds: BoundingBox, padding_m: int = 1000) -> list[POI]:
        lat_pad = padding_m / 111_320
        lon_pad = padding_m / 55_800
        area = (
            f"({bounds.south - lat_pad},{bounds.west - lon_pad},"
            f"{bounds.north + lat_pad},{bounds.east + lon_pad})"
        )
        return await self._fetch(f"[out:json][timeout:40];({_selectors(area)});out center tags;")

    async def _fetch(self, query: str) -> list[POI]:
        key = "overpass:" + hashlib.sha256(query.encode()).hexdigest()
        cached = await self.cache.get_json(key)
        if cached is not None:
            return [POI.model_validate(item) for item in cached]
        try:
            async with httpx.AsyncClient(
                headers={"User-Agent": self.user_agent}, timeout=45
            ) as client:
                response = await client.post(self.url, data={"data": query})
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise OverpassError("OpenStreetMap data provider is unavailable") from exc
        pois = self._normalize(response.json().get("elements", []))
        await self.cache.set_json(key, [p.model_dump(mode="json") for p in pois], self.ttl)
        return pois

    @staticmethod
    def _normalize(elements: list[dict[str, Any]]) -> list[POI]:
        pois: list[POI] = []
        seen: set[str] = set()
        for element in elements:
            osm_id = f"{element.get('type', 'node')}/{element.get('id')}"
            if osm_id in seen:
                continue
            tags = element.get("tags", {})
            category = _category(tags)
            lat = element.get("lat", element.get("center", {}).get("lat"))
            lon = element.get("lon", element.get("center", {}).get("lon"))
            if category is None or lat is None or lon is None:
                continue
            seen.add(osm_id)
            pois.append(
                POI(
                    osm_id=osm_id,
                    category=category,
                    location=Location(latitude=lat, longitude=lon),
                    name=tags.get("name"),
                    tags={str(k): str(v) for k, v in tags.items()},
                )
            )
        return pois
