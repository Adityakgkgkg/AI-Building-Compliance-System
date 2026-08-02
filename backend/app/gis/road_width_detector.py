"""
Road Width Detector
===================
Calculates and verifies effective road width (in meters) for FAR/Setback rules.
"""

from app.gis.road_detector import RoadDetector


class RoadWidthDetector:
    """Evaluates effective road width for compliance rule selection."""

    @staticmethod
    def get_road_width(lat: float, lon: float) -> float:
        road_info = RoadDetector.detect_nearest_road(lat, lon)
        return road_info.road_width
