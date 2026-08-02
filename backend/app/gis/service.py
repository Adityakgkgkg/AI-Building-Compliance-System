"""
GIS Context Intelligence Service
================================
Service layer encapsulating UCIE functionality for API router endpoints.
"""

from typing import Dict, Any, Optional
from app.gis.context_engine import UrbanContextEngine
from app.gis.dataset_manager import DatasetManager
from app.gis.ward_detector import WardDetector
from app.gis.zone_detector import ZoneDetector
from app.gis.road_detector import RoadDetector
from app.gis.lake_detector import LakeDetector
from app.gis.airport_detector import AirportDetector
from app.gis.flood_detector import FloodDetector
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


class GISService:
    """Service layer exposing UCIE operations."""

    @staticmethod
    def get_full_context(req: GISContextRequest) -> GISContextResponse:
        return UrbanContextEngine.evaluate_context(req)

    @staticmethod
    def get_ward(lat: float, lon: float) -> WardResponse:
        return WardDetector.detect_ward(lat, lon)

    @staticmethod
    def get_zone(lat: float, lon: float) -> ZoneResponse:
        ward_res = WardDetector.detect_ward(lat, lon)
        return ZoneDetector.detect_zone(ward_res.ward_name, str(ward_res.ward_number or ""))

    @staticmethod
    def get_road(lat: float, lon: float) -> RoadResponse:
        return RoadDetector.detect_nearest_road(lat, lon)

    @staticmethod
    def get_lake(lat: float, lon: float) -> LakeResponse:
        return LakeDetector.detect_lake_proximity(lat, lon)

    @staticmethod
    def get_airport(lat: float, lon: float) -> AirportResponse:
        return AirportDetector.detect_airport_restriction(lat, lon)

    @staticmethod
    def get_flood(lat: float, lon: float) -> FloodResponse:
        return FloodDetector.detect_flood_risk(lat, lon)

    @staticmethod
    def get_manifest() -> Dict[str, Any]:
        dm = DatasetManager.get_instance()
        if not dm.is_loaded:
            dm.initialize()
        return dm.manifest_data or {}

    @staticmethod
    def get_layer_geojson(layer_name: str) -> Optional[Dict[str, Any]]:
        dm = DatasetManager.get_instance()
        return dm.get_raw_geojson(layer_name)
