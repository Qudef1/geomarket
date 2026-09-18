import pytest
from app.domain.models import POI, BoundingBox, Location, POICategory
from app.services.analysis import AnalysisService


class FakeOverpass:
    def __init__(self) -> None:
        self.calls = 0

    async def in_bounds(self, bounds: BoundingBox, padding_m: int = 1000) -> list[POI]:
        self.calls += 1
        return [
            POI(
                osm_id="node/1",
                category=POICategory.BUS_STOP,
                location=Location(latitude=60.17, longitude=24.94),
            )
        ]


@pytest.mark.asyncio
async def test_area_analysis_fetches_shared_pois_once() -> None:
    overpass = FakeOverpass()
    service = AnalysisService(overpass)  # type: ignore[arg-type]
    results = await service.analyze_area(
        BoundingBox(south=60.16, west=24.93, north=60.17, east=24.94),
        spacing_m=500,
        limit=20,
        top_n=5,
    )
    assert overpass.calls == 1
    assert len(results) <= 5
    assert results == sorted(results, key=lambda item: item.result.score, reverse=True)
