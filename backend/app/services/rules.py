from collections.abc import Callable
from dataclasses import dataclass

from app.domain.models import LocationFeatures, RuleResult


@dataclass(frozen=True)
class Rule:
    name: str
    condition: Callable[[LocationFeatures], bool]
    modifier: float
    reason: Callable[[LocationFeatures], str]

    def evaluate(self, features: LocationFeatures) -> RuleResult:
        triggered = self.condition(features)
        return RuleResult(
            rule=self.name,
            triggered=triggered,
            modifier=self.modifier if triggered else 0.0,
            reason=self.reason(features) if triggered else "Rule condition was not met.",
        )


COFFEE_SHOP_RULES = (
    Rule(
        "university_proximity",
        lambda f: f.universities_1000m >= 2,
        0.08,
        lambda f: f"{f.universities_1000m} universities are within 1 km.",
    ),
    Rule(
        "office_concentration",
        lambda f: f.offices_500m >= 10,
        0.06,
        lambda f: f"{f.offices_500m} offices are within 500 m.",
    ),
    Rule(
        "transport_access",
        lambda f: f.bus_stops_500m >= 8 or f.stations_1000m >= 1,
        0.05,
        lambda f: (
            f"Strong access from {f.bus_stops_500m} bus stops and {f.stations_1000m} stations."
        ),
    ),
    Rule(
        "competition_saturation",
        lambda f: f.cafes_500m >= 15,
        -0.12,
        lambda f: f"High competition from {f.cafes_500m} cafes within 500 m.",
    ),
    Rule(
        "low_activity",
        lambda f: f.poi_density_500m < 3,
        -0.08,
        lambda f: "Very few mapped amenities are nearby; evidence quality is limited.",
    ),
)


class RuleEngine:
    def evaluate(self, features: LocationFeatures) -> list[RuleResult]:
        return [rule.evaluate(features) for rule in COFFEE_SHOP_RULES]
