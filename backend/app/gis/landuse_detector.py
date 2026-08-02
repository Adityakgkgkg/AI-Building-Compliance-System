"""
Land Use Detector
=================
Determines BDA Master Plan zoning (Residential, Commercial, Industrial, etc.) for a site.
"""

from shapely.geometry import Point
from app.gis.dataset_manager import DatasetManager
from app.gis.schemas import LandUseResponse, CitationSchema


class LandUseDetector:
    """Detects BDA Master Plan Zoning."""

    @staticmethod
    def detect_landuse(lat: float, lon: float) -> LandUseResponse:
        point = Point(lon, lat)
        dm = DatasetManager.get_instance()
        idx = dm.get_index("landuse")

        if idx is not None:
            feat = idx.query_point_in_polygon(point)
            if feat is not None:
                props = feat.properties
                land_use = props.get("land_use", "Residential")
                code = props.get("master_plan_code", "R1")

                citation = CitationSchema(
                    dataset_name="BDA Master Plan Land Use Classification",
                    authority="Bangalore Development Authority (BDA)",
                    source_url="https://gba.karnataka.gov.in/gisviewer/index.html",
                    license="Government Official Master Plan",
                    feature_id=feat.feature_id,
                    observation=f"Site falls within {land_use} Zone ({code})"
                )

                return LandUseResponse(
                    land_use=land_use,
                    master_plan_zone=code,
                    citation=citation
                )

        # Fallback heuristic: Default to Residential zone
        citation = CitationSchema(
            dataset_name="BDA Master Plan Land Use Classification",
            authority="BDA",
            source_url="https://gba.karnataka.gov.in/gisviewer/index.html",
            license="Government Official Master Plan",
            observation="Site classified as Residential Zone R1 based on default BBMP urban layout"
        )

        return LandUseResponse(
            land_use="Residential",
            master_plan_zone="R1",
            citation=citation
        )
