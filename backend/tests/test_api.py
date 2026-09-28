from app.api.dependencies import get_analysis_service
from app.domain.models import POI, BoundingBox, Location, POICategory
from app.main import app
from app.services.analysis import AnalysisService
from fastapi.testclient import TestClient


class FakeOverpass:
    async def around(self, location: Location, radius_m: int = 1000) -> list[POI]:
        return [
            POI(
                osm_id="node/1",
                category=POICategory.BUS_STOP,
                location=location,
                name="Test stop",
            )
        ]

    async def in_bounds(self, bounds: BoundingBox, padding_m: int = 1000) -> list[POI]:
        return [
            POI(
                osm_id="node/1",
                category=POICategory.CAFE,
                location=Location(latitude=bounds.south, longitude=bounds.west),
            )
        ]


def fake_service() -> AnalysisService:
    return AnalysisService(FakeOverpass())  # type: ignore[arg-type]


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_accepts_loopback_frontend(client: TestClient) -> None:
    response = client.options(
        "/api/v1/analysis/point",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"


def test_cors_rejects_untrusted_origin(client: TestClient) -> None:
    response = client.options(
        "/api/v1/analysis/point",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 400


def test_business_types(client: TestClient) -> None:
    assert client.get("/api/v1/business-types").json() == [
        {"id": "coffee_shop", "name": "Coffee Shop"}
    ]


def test_point_schema_rejects_bad_coordinates(client: TestClient) -> None:
    response = client.post(
        "/api/v1/analysis/point",
        json={"business_type": "coffee_shop", "latitude": 100, "longitude": 24},
    )
    assert response.status_code == 422


def test_point_analysis_contract(client: TestClient) -> None:
    app.dependency_overrides[get_analysis_service] = fake_service
    try:
        response = client.post(
            "/api/v1/analysis/point",
            json={"business_type": "coffee_shop", "latitude": 60.17, "longitude": 24.94},
        )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    payload = response.json()
    assert payload["result"]["score"] >= 0
    assert payload["pois"][0]["name"] == "Test stop"
    assert payload["result"]["rules"][0]["rule"] == "university_proximity"


def test_area_analysis_returns_ranked_candidates(client: TestClient) -> None:
    app.dependency_overrides[get_analysis_service] = fake_service
    try:
        response = client.post(
            "/api/v1/analysis/area",
            json={
                "business_type": "coffee_shop",
                "bounds": {"south": 60.16, "west": 24.93, "north": 60.17, "east": 24.94},
                "grid_spacing_m": 500,
                "top_n": 3,
            },
        )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    candidates = response.json()["candidates"]
    assert [candidate["rank"] for candidate in candidates] == [1, 2, 3]
    assert candidates[0]["result"]["score"] >= candidates[-1]["result"]["score"]
