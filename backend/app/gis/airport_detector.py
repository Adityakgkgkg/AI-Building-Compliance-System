"""
Airport Height Restriction Detector
====================================
Determines if location falls within Airports Authority of India (AAI) height funnels
for HAL, KIAL, or Yelahanka Air Force Base.
"""

from shapely.geometry import Point
from app.gis.dataset_manager import DatasetManager
from app.gis.schemas import AirportResponse, CitationSchema


class AirportDetector:
    """Detects airport elevation height restrictions."""

    @staticmethod
    def detect_airport_restriction(lat: float, lon: float) -> AirportResponse:
        point = Point(lon, lat)
        dm = DatasetManager.get_instance()
        idx = dm.get_index("airport_buffer")

        if idx is not None:
            feat = idx.query_point_in_polygon(point)
            if feat is not None:
                props = feat.properties
                ap_name = props.get("airport_name", "Airport Authority Zone")
                limit_m = float(props.get("height_limit_meters_agl", 45.0))
                code = props.get("restriction_code", "AAI_ZONE")

                citation = CitationSchema(
                    dataset_name="Airport Height Restriction Funnel",
                    authority="Airports Authority of India (AAI)",
                    source_url="https://gba.karnataka.gov.in/gisviewer/index.html",
                    license="Government Statutory Restriction",
                    feature_id=feat.feature_id,
                    observation=f"Site is inside {ap_name} restriction funnel. Max height limit: {limit_m}m AGL ({code})"
                )

                return AirportResponse(
                    airport_zone=True,
                    airport_height_limit=limit_m,
                    nearest_airport_name=ap_name,
                    citation=citation
                )

        citation = CitationSchema(
            dataset_name="Airport Height Restriction Funnel",
            authority="Airports Authority of India (AAI)",
            source_url="https://gba.karnataka.gov.in/gisviewer/index.html",
            license="Government Statutory Restriction",
            observation="Site lies outside restricted airport approach funnels"
        )

        return AirportResponse(
            airport_zone=False,
            airport_height_limit=None,
            nearest_airport_name="None Restricted",
            citation=citation
        )
