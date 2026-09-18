from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


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
