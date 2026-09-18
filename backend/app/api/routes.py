from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_analysis_service, get_geocoder
from app.api.schemas import (
    AreaAnalysisRequest,
    AreaAnalysisResponse,
    CandidateResponse,
    PointAnalysisRequest,
    PointAnalysisResponse,
)
from app.core.config import get_settings
from app.domain.models import BusinessType, Location
from app.integrations.geocoding import GeocodingError, NominatimClient
from app.integrations.overpass import OverpassError
from app.services.analysis import AnalysisService

router = APIRouter(prefix="/api/v1")
AnalysisDep = Annotated[AnalysisService, Depends(get_analysis_service)]
GeocoderDep = Annotated[NominatimClient, Depends(get_geocoder)]


@router.get("/business-types", response_model=list[dict[str, str]])
async def business_types() -> list[dict[str, str]]:
    return [{"id": BusinessType.COFFEE_SHOP, "name": "Coffee Shop"}]


@router.get("/geo/search", response_model=list[dict[str, Any]])
async def geo_search(
    geocoder: GeocoderDep, q: str = Query(min_length=2, max_length=200)
) -> list[dict[str, Any]]:
    try:
        return await geocoder.search(q)
    except GeocodingError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/analysis/point", response_model=PointAnalysisResponse)
async def analyze_point(
    request: PointAnalysisRequest, service: AnalysisDep
) -> PointAnalysisResponse:
    location = Location(latitude=request.latitude, longitude=request.longitude)
    try:
        result, pois = await service.analyze_point(location, request.radius_m)
    except OverpassError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return PointAnalysisResponse(
        location=location, business_type=request.business_type, result=result, pois=pois
    )


@router.post("/analysis/area", response_model=AreaAnalysisResponse)
async def analyze_area(request: AreaAnalysisRequest, service: AnalysisDep) -> AreaAnalysisResponse:
    try:
        candidates = await service.analyze_area(
            request.bounds,
            request.grid_spacing_m,
            get_settings().max_candidates,
            request.top_n,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except OverpassError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return AreaAnalysisResponse(
        business_type=request.business_type,
        candidates=[
            CandidateResponse(rank=index, location=item.location, result=item.result)
            for index, item in enumerate(candidates, 1)
        ],
    )
