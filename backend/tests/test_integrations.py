import httpx
import pytest
from app.domain.models import POICategory
from app.integrations.cache import MemoryCache, RedisCache
from app.integrations.geocoding import NominatimClient
from app.integrations.overpass import OverpassClient
from redis.exceptions import ConnectionError as RedisConnectionError


def test_overpass_normalizes_nodes_and_ways() -> None:
    elements = [
        None,
        {"type": "node", "lat": 60.1, "lon": 24.9, "tags": {"amenity": "cafe"}},
        {
            "type": "node",
            "id": 1,
            "lat": 60.1,
            "lon": 24.9,
            "tags": {"amenity": "cafe", "name": "A"},
        },
        {
            "type": "way",
            "id": 2,
            "center": {"lat": 60.2, "lon": 25.0},
            "tags": {"office": "company"},
        },
        {"type": "node", "id": 3, "lat": 60.2, "lon": 25.0, "tags": {}},
    ]
    pois = OverpassClient._normalize(elements)
    assert [poi.category for poi in pois] == [POICategory.CAFE, POICategory.OFFICE]
    assert pois[1].osm_id == "way/2"


def test_overpass_skips_invalid_external_coordinates() -> None:
    elements = [
        {
            "type": "node",
            "id": 1,
            "lat": 1000,
            "lon": 24.9,
            "tags": {"amenity": "cafe"},
        },
        {
            "type": "node",
            "id": 2,
            "lat": 60.1,
            "lon": 24.9,
            "tags": {"amenity": "cafe"},
        },
    ]

    pois = OverpassClient._normalize(elements)

    assert [poi.osm_id for poi in pois] == ["node/2"]


@pytest.mark.asyncio
async def test_overpass_falls_back_after_transient_provider_error() -> None:
    requested_hosts: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requested_hosts.append(request.url.host)
        if request.url.host == "primary.example":
            return httpx.Response(504, request=request)
        return httpx.Response(200, request=request, json={"elements": []})

    client = OverpassClient(
        "https://primary.example/api",
        "tests",
        MemoryCache(),
        60,
        ("https://fallback.example/api",),
        httpx.MockTransport(handler),
    )

    assert await client._fetch("[out:json];node(0,0,1,1);out;") == []
    assert requested_hosts == ["primary.example", "fallback.example"]


@pytest.mark.asyncio
async def test_overpass_does_not_retry_invalid_queries() -> None:
    requested_hosts: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requested_hosts.append(request.url.host)
        return httpx.Response(400, request=request)

    client = OverpassClient(
        "https://primary.example/api",
        "tests",
        MemoryCache(),
        60,
        ("https://fallback.example/api",),
        httpx.MockTransport(handler),
    )

    with pytest.raises(RuntimeError, match="unavailable"):
        await client._fetch("invalid")
    assert requested_hosts == ["primary.example"]


@pytest.mark.asyncio
async def test_geocoder_uses_cache() -> None:
    cache = MemoryCache()
    await cache.set_json("geocode:kamppi:5", [{"display_name": "cached"}], 60)
    client = NominatimClient("https://example.invalid", "tests", cache, 60)
    assert await client.search("Kamppi") == [{"display_name": "cached"}]


@pytest.mark.asyncio
async def test_geocoder_wraps_network_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fail(*args: object, **kwargs: object) -> httpx.Response:
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(httpx.AsyncClient, "get", fail)
    client = NominatimClient("https://example.invalid", "tests", MemoryCache(), 60)
    with pytest.raises(RuntimeError, match="unavailable"):
        await client.search("Kamppi")


@pytest.mark.asyncio
async def test_geocoder_skips_invalid_provider_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def respond(*args: object, **kwargs: object) -> httpx.Response:
        request = httpx.Request("GET", "https://example.invalid/search")
        return httpx.Response(
            200,
            request=request,
            json=[
                {"display_name": "Invalid", "lat": "not-a-number", "lon": "24.9"},
                {"display_name": "Outside Earth", "lat": "100", "lon": "24.9"},
                {"display_name": "Kamppi", "lat": "60.169", "lon": "24.932"},
            ],
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", respond)
    client = NominatimClient("https://example.invalid", "tests", MemoryCache(), 60)

    assert await client.search("  Kamppi  ") == [
        {
            "display_name": "Kamppi",
            "latitude": 60.169,
            "longitude": 24.932,
            "type": None,
        }
    ]


@pytest.mark.asyncio
async def test_redis_cache_failure_is_treated_as_a_cache_miss() -> None:
    class UnavailableRedis:
        async def get(self, key: str) -> str | None:
            raise RedisConnectionError("offline")

        async def set(self, key: str, value: str, ex: int) -> None:
            raise RedisConnectionError("offline")

    cache = RedisCache(UnavailableRedis())  # type: ignore[arg-type]

    assert await cache.get_json("test") is None
    await cache.set_json("test", {"ok": True}, 60)
