"""
GIS Context Intelligence API Router
===================================
FastAPI routes for municipal urban context lookup, layer streaming, and manifest verification.
"""

from typing import Dict, Any
from fastapi import APIRouter, Query, HTTPException, status
from app.gis.schemas import (
    GISContextRequest,
    GISContextResponse,
    WardResponse,
    ZoneResponse,
    RoadResponse,
    LakeResponse,
    AirportResponse,
    FloodResponse,
)
from app.gis.service import GISService

router = APIRouter(prefix="/gis", tags=["Urban Context Intelligence Engine (GIS)"])


@router.post(
    "/context",
    response_model=GISContextResponse,
    summary="Evaluate Full Urban Context",
    description="Automatically determines administrative boundaries, road network width, zoning, lake buffers, and statutory restrictions for building plan compliance."
)
async def evaluate_urban_context(payload: GISContextRequest) -> GISContextResponse:
    try:
        return GISService.get_full_context(payload)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate GIS urban context: {str(exc)}"
        )


@router.get(
    "/ward",
    response_model=WardResponse,
    summary="Detect BBMP Ward",
    description="Detects BBMP Ward name and ward number for given latitude/longitude."
)
async def get_ward(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude")
) -> WardResponse:
    return GISService.get_ward(lat, lon)


@router.get(
    "/zone",
    response_model=ZoneResponse,
    summary="Detect BBMP Zone",
    description="Detects BBMP Administrative Zone mapping."
)
async def get_zone(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0)
) -> ZoneResponse:
    return GISService.get_zone(lat, lon)


@router.get(
    "/road",
    response_model=RoadResponse,
    summary="Detect Nearest Road & Road Width",
    description="Determines nearest public road name, classification, and effective width in meters."
)
async def get_road(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0)
) -> RoadResponse:
    return GISService.get_road(lat, lon)


@router.get(
    "/lake",
    response_model=LakeResponse,
    summary="Detect Lake & Water Buffer Clearance",
    description="Calculates distance to nearest water body/lake and storm drain, evaluating 30m/75m buffer compliance."
)
async def get_lake(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0)
) -> LakeResponse:
    return GISService.get_lake(lat, lon)


@router.get(
    "/airport",
    response_model=AirportResponse,
    summary="Detect Airport Height Restrictions",
    description="Checks if site lies within HAL/KIAL/Yelahanka airport height limitation funnels."
)
async def get_airport(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0)
) -> AirportResponse:
    return GISService.get_airport(lat, lon)


@router.get(
    "/flood",
    response_model=FloodResponse,
    summary="Detect Municipal Flood Risk",
    description="Evaluates municipal flood risk level (Low, Medium, High)."
)
async def get_flood(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0)
) -> FloodResponse:
    return GISService.get_flood(lat, lon)


@router.get(
    "/manifest",
    summary="Get GIS Datasets Provenance Manifest",
    description="Returns JSON manifest containing dataset lineage, SHA256 checksums, authority sources, and geometry counts."
)
async def get_manifest() -> Dict[str, Any]:
    return GISService.get_manifest()


@router.get(
    "/layers/{layer_name}",
    summary="Get Layer GeoJSON for Frontend Map",
    description="Returns raw EPSG:4326 GeoJSON feature collection for interactive Leaflet visual rendering."
)
async def get_layer_geojson(layer_name: str) -> Dict[str, Any]:
    data = GISService.get_layer_geojson(layer_name)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Spatial layer '{layer_name}' not found."
        )
    return data
