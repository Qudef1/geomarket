from abc import ABC, abstractmethod

from app.configuration import COFFEE_SHOP_PROFILE
from app.domain.models import LocationFeatures, ModelPrediction, ScoreComponents


def _saturate(value: float, good_at: float) -> float:
    return min(max(value / good_at, 0.0), 1.0)


class LocationScoringModel(ABC):
    @abstractmethod
    def predict(self, features: LocationFeatures) -> ModelPrediction: ...


class BaselineScoringModel(LocationScoringModel):
    """Deterministic, documented fallback that requires no fabricated labels."""

    def predict(self, features: LocationFeatures) -> ModelPrediction:
        components = ScoreComponents(
            competition=max(0.0, 1.0 - _saturate(features.cafes_500m, 20)),
            transport=_saturate(features.bus_stops_500m + 3 * features.stations_1000m, 15),
            target_audience=_saturate(4 * features.universities_1000m + features.offices_1000m, 25),
            commercial_activity=_saturate(features.restaurants_500m + features.offices_500m, 25),
            centrality=max(0.0, 1.0 - features.distance_to_center_km / 10),
            amenities=_saturate(features.parking_500m + features.supermarkets_1000m, 8),
        )
        values = components.model_dump()
        score = sum(values[name] * weight for name, weight in COFFEE_SHOP_PROFILE.weights.items())
        observed = min(1.0, features.poi_density_500m / 20)
        return ModelPrediction(
            score=round(score, 4),
            confidence=round(0.55 + observed * 0.35, 3),
            components=components,
            model_name="deterministic_baseline_v1",
        )
