from dataclasses import dataclass

from app.domain.models import POI, BoundingBox, Location, LocationScore
from app.integrations.overpass import OverpassClient
from app.ml.models import BaselineScoringModel, LocationScoringModel
from app.services.decision import DecisionEngine
from app.services.features import FeatureEngine
from app.services.geo import generate_grid
from app.services.rules import RuleEngine

HELSINKI_CENTER = Location(latitude=60.1699, longitude=24.9384)


@dataclass(frozen=True)
class CandidateResult:
    location: Location
    result: LocationScore


class AnalysisService:
    def __init__(
        self,
        overpass: OverpassClient,
        feature_engine: FeatureEngine | None = None,
        scoring_model: LocationScoringModel | None = None,
        rule_engine: RuleEngine | None = None,
        decision_engine: DecisionEngine | None = None,
    ) -> None:
        self.overpass = overpass
        self.features = feature_engine or FeatureEngine()
        self.model = scoring_model or BaselineScoringModel()
        self.rules = rule_engine or RuleEngine()
        self.decisions = decision_engine or DecisionEngine()

    def score(self, location: Location, pois: list[POI]) -> LocationScore:
        features = self.features.extract(location, pois, HELSINKI_CENTER)
        return self.decisions.decide(
            features, self.model.predict(features), self.rules.evaluate(features)
        )

    async def analyze_point(
        self, location: Location, radius_m: int
    ) -> tuple[LocationScore, list[POI]]:
        pois = await self.overpass.around(location, radius_m)
        return self.score(location, pois), pois

    async def analyze_area(
        self, bounds: BoundingBox, spacing_m: int, limit: int, top_n: int
    ) -> list[CandidateResult]:
        candidates = generate_grid(bounds, spacing_m, limit)
        pois = await self.overpass.in_bounds(bounds)  # one shared fetch, never N per candidate
        results = [CandidateResult(point, self.score(point, pois)) for point in candidates]
        results.sort(key=lambda item: item.result.score, reverse=True)
        return results[:top_n]
