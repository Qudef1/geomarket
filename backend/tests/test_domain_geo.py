import pytest
from app.domain.models import BoundingBox, Location
from app.services.geo import distance_m, generate_grid
from pydantic import ValidationError


def test_location_rejects_invalid_coordinates() -> None:
    with pytest.raises(ValidationError):
        Location(latitude=91, longitude=0)


def test_distance_is_geographically_plausible() -> None:
    a = Location(latitude=60.1699, longitude=24.9384)
    b = Location(latitude=60.1709, longitude=24.9384)
    assert distance_m(a, b) == pytest.approx(111.2, abs=0.5)


def test_grid_respects_limit() -> None:
    bounds = BoundingBox(south=60.16, west=24.92, north=60.18, east=24.96)
    with pytest.raises(ValueError, match="more than 2"):
        generate_grid(bounds, 500, 2)
