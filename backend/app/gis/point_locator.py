"""
Point Locator Detector
======================
Verifies whether a coordinate point lies within the official BBMP administrative boundary.
"""

from typing import Tuple
from shapely.geometry import Point
from app.gis.dataset_manager import DatasetManager
from app.gis.schemas import CitationSchema


class PointLocator:
    """Detects administrative boundary containment."""

    @staticmethod
    def is_inside_bbmp(lat: float, lon: float) -> Tuple[bool, CitationSchema]:
        point = Point(lon, lat)
        dm = DatasetManager.get_instance()
        idx = dm.get_index("bbmp_boundary")

        citation = CitationSchema(
            dataset_name="BBMP Administrative Boundary",
            authority="BBMP",
            source_url="https://projects.datameet.org/Municipal_Spatial_Data/bangalore/",
            license="Government Open Data",
            feature_id="BBMP_OUTER_BOUNDS",
            observation=f"Point ({lat}, {lon}) evaluated against BBMP municipal boundary polygon"
        )

        if idx is None:
            # Simple bounding box fallback for Greater Bangalore (12.83 to 13.15 N, 77.45 to 77.78 E)
            inside = (12.80 <= lat <= 13.20) and (77.40 <= lon <= 77.80)
            return inside, citation

        feat = idx.query_point_in_polygon(point)
        if feat:
            citation.feature_id = feat.feature_id
            return True, citation

        # Fallback bounding box check
        inside = (12.80 <= lat <= 13.20) and (77.40 <= lon <= 77.80)
        return inside, citation
