from pydantic import BaseModel, Field

from app.domain.models import POI, BoundingBox, BusinessType, Location, LocationScore


class PointAnalysisRequest(BaseModel):
    business_type: BusinessType
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    radius_m: int = Field(default=1000, ge=250, le=2000)
    target_audience: list[str] = Field(default_factory=list, max_length=10)


class PointAnalysisResponse(BaseModel):
    location: Location
    business_type: BusinessType
    result: LocationScore
    pois: list[POI]


class AreaAnalysisRequest(BaseModel):
    business_type: BusinessType
    bounds: BoundingBox
    grid_spacing_m: int = Field(default=500, ge=100, le=2000)
    top_n: int = Field(default=10, ge=1, le=20)


class CandidateResponse(BaseModel):
    rank: int
    location: Location
    result: LocationScore


class AreaAnalysisResponse(BaseModel):
    business_type: BusinessType
    candidates: list[CandidateResponse]
