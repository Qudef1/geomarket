from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BusinessType(StrEnum):
    COFFEE_SHOP = "coffee_shop"


class Location(BaseModel):
    model_config = ConfigDict(frozen=True)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class BoundingBox(BaseModel):
    south: float = Field(ge=-90, le=90)
    west: float = Field(ge=-180, le=180)
    north: float = Field(ge=-90, le=90)
    east: float = Field(ge=-180, le=180)

    @field_validator("north")
    @classmethod
    def north_is_valid(cls, value: float, info: Any) -> float:
        if "south" in info.data and value <= info.data["south"]:
            raise ValueError("north must be greater than south")
        return value

    @field_validator("east")
    @classmethod
    def east_is_valid(cls, value: float, info: Any) -> float:
        if "west" in info.data and value <= info.data["west"]:
            raise ValueError("east must be greater than west")
        return value


class POICategory(StrEnum):
    CAFE = "cafe"
    RESTAURANT = "restaurant"
    UNIVERSITY = "university"
    BUS_STOP = "bus_stop"
    STATION = "station"
    OFFICE = "office"
    PARKING = "parking"
    SUPERMARKET = "supermarket"


class POI(BaseModel):
    model_config = ConfigDict(frozen=True)
    osm_id: str
    category: POICategory
    location: Location
    name: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)


class LocationFeatures(BaseModel):
    cafes_250m: int = 0
    cafes_500m: int = 0
    cafes_1000m: int = 0
    restaurants_500m: int = 0
    universities_500m: int = 0
    universities_1000m: int = 0
    bus_stops_250m: int = 0
    bus_stops_500m: int = 0
    stations_1000m: int = 0
    offices_500m: int = 0
    offices_1000m: int = 0
    parking_500m: int = 0
    supermarkets_1000m: int = 0
    distance_to_center_km: float = 0.0
    poi_density_500m: float = 0.0


class ScoreComponents(BaseModel):
    competition: float
    transport: float
    target_audience: float
    commercial_activity: float
    centrality: float
    amenities: float


class ModelPrediction(BaseModel):
    score: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    components: ScoreComponents
    model_name: str


class RuleResult(BaseModel):
    rule: str
    triggered: bool
    modifier: float
    reason: str


class LocationScore(BaseModel):
    score: float = Field(ge=0, le=1)
    grade: str
    base_score: float
    rule_adjustment: float
    confidence: float
    components: ScoreComponents
    features: LocationFeatures
    rules: list[RuleResult]
    positive_factors: list[str]
    negative_factors: list[str]
