import math

from app.domain.models import POI, Location, LocationFeatures, POICategory
from app.services.geo import distance_m


class FeatureEngine:
    def extract(
        self, location: Location, pois: list[POI], city_center: Location
    ) -> LocationFeatures:
        distances = [(poi, distance_m(location, poi.location)) for poi in pois]

        def count(category: POICategory, radius: int) -> int:
            return sum(
                1 for poi, distance in distances if poi.category == category and distance <= radius
            )

        within_500 = sum(1 for _, distance in distances if distance <= 500)
        area_km2 = math.pi * 0.5**2
        return LocationFeatures(
            cafes_250m=count(POICategory.CAFE, 250),
            cafes_500m=count(POICategory.CAFE, 500),
            cafes_1000m=count(POICategory.CAFE, 1000),
            restaurants_500m=count(POICategory.RESTAURANT, 500),
            universities_500m=count(POICategory.UNIVERSITY, 500),
            universities_1000m=count(POICategory.UNIVERSITY, 1000),
            bus_stops_250m=count(POICategory.BUS_STOP, 250),
            bus_stops_500m=count(POICategory.BUS_STOP, 500),
            stations_1000m=count(POICategory.STATION, 1000),
            offices_500m=count(POICategory.OFFICE, 500),
            offices_1000m=count(POICategory.OFFICE, 1000),
            parking_500m=count(POICategory.PARKING, 500),
            supermarkets_1000m=count(POICategory.SUPERMARKET, 1000),
            distance_to_center_km=round(distance_m(location, city_center) / 1000, 3),
            poi_density_500m=round(within_500 / area_km2, 3),
        )
