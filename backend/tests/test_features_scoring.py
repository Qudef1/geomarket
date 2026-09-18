from app.domain.models import POI, Location, POICategory
from app.ml.models import BaselineScoringModel
from app.services.decision import DecisionEngine
from app.services.features import FeatureEngine
from app.services.rules import RuleEngine


def poi(identifier: str, category: POICategory, latitude: float = 60.17) -> POI:
    return POI(
        osm_id=identifier,
        category=category,
        location=Location(latitude=latitude, longitude=24.9384),
    )


def test_feature_pipeline_and_decision_are_traceable() -> None:
    location = Location(latitude=60.1699, longitude=24.9384)
    pois = [
        *[poi(f"bus/{i}", POICategory.BUS_STOP) for i in range(8)],
        *[poi(f"office/{i}", POICategory.OFFICE) for i in range(10)],
        poi("uni/1", POICategory.UNIVERSITY),
        poi("uni/2", POICategory.UNIVERSITY),
        poi("market/1", POICategory.SUPERMARKET),
    ]
    features = FeatureEngine().extract(location, pois, location)
    assert features.bus_stops_500m == 8
    assert features.universities_1000m == 2
    prediction = BaselineScoringModel().predict(features)
    rules = RuleEngine().evaluate(features)
    result = DecisionEngine().decide(features, prediction, rules)
    assert 0 <= result.score <= 1
    assert result.rule_adjustment == 0.19
    assert "2 universities" in result.positive_factors[0]


def test_competition_reduces_score() -> None:
    location = Location(latitude=60.1699, longitude=24.9384)
    cafes = [poi(f"cafe/{i}", POICategory.CAFE) for i in range(15)]
    features = FeatureEngine().extract(location, cafes, location)
    results = RuleEngine().evaluate(features)
    competition = next(result for result in results if result.rule == "competition_saturation")
    assert competition.triggered
    assert competition.modifier == -0.12
