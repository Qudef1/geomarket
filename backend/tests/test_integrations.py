import httpx
import pytest
from app.domain.models import POICategory
from app.integrations.cache import MemoryCache
from app.integrations.geocoding import NominatimClient
from app.integrations.overpass import OverpassClient


def test_overpass_normalizes_nodes_and_ways() -> None:
    elements = [
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
