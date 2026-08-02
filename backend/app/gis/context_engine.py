"""
Urban Context Intelligence Engine (UCIE)
========================================
Master Context Engine Orchestrator for BBMP Municipal Building Approval.

Automatically resolves all spatial context needed for rule engine compliance checking:
- Administrative Boundaries (BBMP, Ward, Zone)
- Road Network & Effective Road Width
- Zoning Land Use Classification
- Environmental Restrictions (Lake 30m/75m Buffers, Storm Drains)
- Statutory Constraints (Airport Height Funnels, Flood Risk)
- Verifiable Approval Report Section Generator with Datasets Citations
"""

import time
import logging
from typing import Optional, List
from app.gis.cache import GISCache
from app.gis.point_locator import PointLocator
from app.gis.ward_detector import WardDetector
from app.gis.zone_detector import ZoneDetector
from app.gis.road_detector import RoadDetector
from app.gis.landuse_detector import LandUseDetector
from app.gis.lake_detector import LakeDetector
from app.gis.airport_detector import AirportDetector
from app.gis.flood_detector import FloodDetector
from app.gis.schemas import GISContextRequest, GISContextResponse, CitationSchema

logger = logging.getLogger("app.gis.context_engine")


class UrbanContextEngine:
    """Master spatial engine orchestrator."""

    @staticmethod
    def evaluate_context(req: GISContextRequest) -> GISContextResponse:
        lat = req.latitude
        lon = req.longitude
        start_t = time.perf_counter()

        # Check Cache
        cached = GISCache.get(lat, lon)
        if cached is not None:
            logger.info(f"GIS Cache hit for location ({lat}, {lon})")
            return cached

        citations: List[CitationSchema] = []

        # 1. Point Locator (Inside BBMP)
        is_inside_bbmp, bbmp_cit = PointLocator.is_inside_bbmp(lat, lon)
        citations.append(bbmp_cit)

        # 2. Ward Detector
        ward_res = WardDetector.detect_ward(lat, lon)
        if ward_res.citation:
            citations.append(ward_res.citation)

        # 3. Zone Detector
        zone_res = ZoneDetector.detect_zone(ward_res.ward_name, str(ward_res.ward_number or ""))
        if zone_res.citation:
            citations.append(zone_res.citation)

        # 4. Road Detector
        road_res = RoadDetector.detect_nearest_road(lat, lon)
        if road_res.citation:
            citations.append(road_res.citation)

        # 5. Land Use Detector
        landuse_res = LandUseDetector.detect_landuse(lat, lon)
        if landuse_res.citation:
            citations.append(landuse_res.citation)

        # 6. Lake & Buffer Detector
        lake_res = LakeDetector.detect_lake_proximity(lat, lon)
        if lake_res.citation:
            citations.append(lake_res.citation)

        # 7. Airport Restriction Detector
        airport_res = AirportDetector.detect_airport_restriction(lat, lon)
        if airport_res.citation:
            citations.append(airport_res.citation)

        # 8. Flood Risk Detector
        flood_res = FloodDetector.detect_flood_risk(lat, lon)
        if flood_res.citation:
            citations.append(flood_res.citation)

        exec_time_ms = round((time.perf_counter() - start_t) * 1000.0, 2)

        # 9. Format Verifiable Municipal Approval Report Section
        ward_str = f"Ward {ward_res.ward_number} ({ward_res.ward_name})" if ward_res.ward_number else ward_res.ward_name
        lake_status_str = (
            f"within a regulated lake/drain buffer zone (lake distance: {lake_res.lake_distance}m)"
            if lake_res.lake_buffer
            else f"outside restricted lake buffer zones (nearest lake distance: {lake_res.lake_distance}m)"
        )
        airport_status_str = (
            f"inside the {airport_res.nearest_airport_name} height restriction zone (limit: {airport_res.airport_height_limit}m AGL)"
            if airport_res.airport_zone
            else "outside airport height restriction zones"
        )

        approval_report_text = (
            f"The proposed building site lies within BBMP {zone_res.zone}, {ward_str}. "
            f"The nearest public road is {road_res.road_name} with an estimated width of {road_res.road_width} m. "
            f"According to BDA Master Plan zoning, the site is classified under '{landuse_res.land_use}' land use. "
            f"Spatial environmental analysis confirms the site is {lake_status_str} and is {airport_status_str}. "
            f"The municipal flood risk level is classified as '{flood_res.flood_risk}' based on proximity to storm water channels ({lake_res.storm_drain_distance}m)."
        )

        response = GISContextResponse(
            city="Bangalore",
            authority="BBMP",
            zone=zone_res.zone,
            ward=ward_res.ward_name,
            ward_number=ward_res.ward_number,
            road_name=road_res.road_name,
            road_width=road_res.road_width,
            land_use=landuse_res.land_use,
            lake_distance=lake_res.lake_distance,
            lake_buffer=lake_res.lake_buffer,
            airport_zone=airport_res.airport_zone,
            airport_height_limit=airport_res.airport_height_limit,
            flood_risk=flood_res.flood_risk,
            heritage_zone=False,
            storm_drain_distance=lake_res.storm_drain_distance,
            is_inside_bbmp=is_inside_bbmp,
            approval_report_text=approval_report_text,
            citations=citations,
            execution_time_ms=exec_time_ms
        )

        # Cache result
        GISCache.set(lat, lon, response)

        logger.info(
            f"GIS Decision Log | Location: ({lat}, {lon}) | Ward: {ward_res.ward_name} | "
            f"Zone: {zone_res.zone} | Road: {road_res.road_name} ({road_res.road_width}m) | "
            f"LakeDist: {lake_res.lake_distance}m | ExecTime: {exec_time_ms}ms"
        )

        return response
