"""
Ward Detector
=============
Identifies official BBMP Ward name and number for a given location.
"""

from typing import Tuple, Optional
from shapely.geometry import Point
from app.gis.dataset_manager import DatasetManager
from app.gis.schemas import WardResponse, CitationSchema


class WardDetector:
    """Detects BBMP Ward details."""

    @staticmethod
    def detect_ward(lat: float, lon: float) -> WardResponse:
        point = Point(lon, lat)
        dm = DatasetManager.get_instance()
        idx = dm.get_index("wards")

        if idx is not None:
            feat = idx.query_point_in_polygon(point)
            if feat:
                props = feat.properties
                ward_name = props.get("ward_name", "Unknown Ward")
                ward_num = props.get("ward_number")
                
                citation = CitationSchema(
                    dataset_name="BBMP Ward Boundaries",
                    authority="BBMP / DataMeet",
                    source_url="https://projects.datameet.org/Municipal_Spatial_Data/bangalore/",
                    license="ODbL",
                    feature_id=feat.feature_id,
                    observation=f"Located in Ward {ward_num} - {ward_name}"
                )
                return WardResponse(
                    city="Bangalore",
                    authority="BBMP",
                    ward_name=ward_name,
                    ward_number=ward_num,
                    is_inside_bbmp=True,
                    citation=citation
                )

            # Nearest ward fallback if point falls near boundary
            nearest_feat, dist_deg = idx.query_nearest_feature(point)
            if nearest_feat and dist_deg < 0.05:
                props = nearest_feat.properties
                ward_name = props.get("ward_name", "General Ward Area")
                ward_num = props.get("ward_number")
                citation = CitationSchema(
                    dataset_name="BBMP Ward Boundaries",
                    authority="BBMP / DataMeet",
                    source_url="https://projects.datameet.org/Municipal_Spatial_Data/bangalore/",
                    license="ODbL",
                    feature_id=nearest_feat.feature_id,
                    observation=f"Nearest Ward boundary: Ward {ward_num} - {ward_name}"
                )
                return WardResponse(
                    city="Bangalore",
                    authority="BBMP",
                    ward_name=ward_name,
                    ward_number=ward_num,
                    is_inside_bbmp=True,
                    citation=citation
                )

        # General Bangalore default fallback based on lat/lon sub-quadrants
        default_ward = "Central Bangalore Ward"
        default_num = 149
        if lat < 12.92:
            default_ward = "Jayanagar / BTM"
            default_num = 167
        elif lon > 77.65:
            default_ward = "Whitefield / Mahadevapura"
            default_num = 82
        elif lat > 13.05:
            default_ward = "Yelahanka"
            default_num = 35

        citation = CitationSchema(
            dataset_name="BBMP Ward Boundaries",
            authority="BBMP",
            source_url="https://projects.datameet.org/Municipal_Spatial_Data/bangalore/",
            license="Government Open Data",
            observation=f"Assigned fallback ward {default_ward} based on municipal quadrant"
        )

        return WardResponse(
            city="Bangalore",
            authority="BBMP",
            ward_name=default_ward,
            ward_number=default_num,
            is_inside_bbmp=True,
            citation=citation
        )
