import math

from app.domain.models import BoundingBox, Location

EARTH_RADIUS_M = 6_371_008.8


def distance_m(a: Location, b: Location) -> float:
    lat1, lat2 = math.radians(a.latitude), math.radians(b.latitude)
    dlat = lat2 - lat1
    dlon = math.radians(b.longitude - a.longitude)
    hav = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(hav))


def generate_grid(bounds: BoundingBox, spacing_m: int, limit: int) -> list[Location]:
    if not 100 <= spacing_m <= 2000:
        raise ValueError("grid spacing must be between 100 and 2000 metres")
    mid_lat = (bounds.south + bounds.north) / 2
    lat_step = spacing_m / 111_320
    lon_step = spacing_m / (111_320 * max(math.cos(math.radians(mid_lat)), 0.01))
    points: list[Location] = []
    latitude = bounds.south
    while latitude <= bounds.north:
        longitude = bounds.west
        while longitude <= bounds.east:
            points.append(Location(latitude=latitude, longitude=longitude))
            if len(points) > limit:
                raise ValueError(f"area produces more than {limit} candidates")
            longitude += lon_step
        latitude += lat_step
    return points
