"""
Flood Risk Detector
===================
Evaluates municipal flood risk (Low, Medium, High) based on distance to primary canals & lakes.
"""

from app.gis.lake_detector import LakeDetector
from app.gis.schemas import FloodResponse, CitationSchema


class FloodDetector:
    """Detects municipal flood risk zone classification."""

    @staticmethod
    def detect_flood_risk(lat: float, lon: float) -> FloodResponse:
        lake_res = LakeDetector.detect_lake_proximity(lat, lon)
        drain_dist = lake_res.storm_drain_distance
        lake_dist = lake_res.lake_distance

        if drain_dist <= 30.0 or lake_dist <= 30.0:
            risk = "High"
        elif drain_dist <= 75.0 or lake_dist <= 75.0:
            risk = "Medium"
        else:
            risk = "Low"

        citation = CitationSchema(
            dataset_name="Bangalore Flood & Topographic Vulnerability Model",
            authority="BBMP Storm Water Drain (SWD) Department",
            source_url="https://site.bbmp.gov.in/",
            license="Government Open Data",
            observation=f"Flood risk evaluated as '{risk}' based on drain distance ({drain_dist}m) and lake distance ({lake_dist}m)"
        )

        return FloodResponse(
            flood_risk=risk,
            proximity_to_drain_meters=drain_dist,
            citation=citation
        )
