from dataclasses import dataclass

from app.domain.models import POICategory

POI_TAGS: dict[POICategory, tuple[tuple[str, str], ...]] = {
    POICategory.CAFE: (("amenity", "cafe"),),
    POICategory.RESTAURANT: (("amenity", "restaurant"),),
    POICategory.UNIVERSITY: (("amenity", "university"), ("amenity", "college")),
    POICategory.BUS_STOP: (("highway", "bus_stop"),),
    POICategory.STATION: (("railway", "station"), ("station", "subway")),
    POICategory.OFFICE: (("office", "*"),),
    POICategory.PARKING: (("amenity", "parking"),),
    POICategory.SUPERMARKET: (("shop", "supermarket"),),
}


@dataclass(frozen=True)
class CoffeeShopProfile:
    weights: dict[str, float]


COFFEE_SHOP_PROFILE = CoffeeShopProfile(
    weights={
        "transport": 0.20,
        "target_audience": 0.25,
        "competition": 0.15,
        "commercial_activity": 0.15,
        "centrality": 0.10,
        "amenities": 0.15,
    }
)
