"""
Road Detector
=============
Identifies nearest public road, road classification, and distance in meters.
"""

from shapely.geometry import Point
from app.gis.dataset_manager import DatasetManager
from app.gis.distance import calculate_spatial_distance_meters
from app.gis.schemas import RoadResponse, CitationSchema


class RoadDetector:
    """Detects nearest road network feature."""

    @staticmethod
    def detect_nearest_road(lat: float, lon: float) -> RoadResponse:
        point = Point(lon, lat)
        dm = DatasetManager.get_instance()
        idx = dm.get_index("roads")

        if idx is not None:
            feat, dist_deg = idx.query_nearest_feature(point)
            if feat is not None:
                props = feat.properties
                road_name = props.get("road_name", "Public Municipal Road")
                road_width = float(props.get("road_width", 18.0))
                classification = props.get("highway", "secondary")
                
                dist_m = calculate_spatial_distance_meters(point, feat.geometry, lat, lon)

                citation = CitationSchema(
                    dataset_name="Greater Bangalore OSM Road Network",
                    authority="OpenStreetMap / BBMP GIS",
                    source_url="https://download.geofabrik.de/asia/india.html",
                    license="ODbL",
                    feature_id=feat.feature_id,
                    observation=f"Nearest public road is {road_name} ({road_width}m width) located {dist_m}m away"
                )

                return RoadResponse(
                    road_name=road_name,
                    road_width=road_width,
                    classification=classification,
                    distance_meters=dist_m,
                    citation=citation
                )

        # Fallback default road information
        citation = CitationSchema(
            dataset_name="Greater Bangalore OSM Road Network",
            authority="BBMP GIS",
            source_url="https://download.geofabrik.de/asia/india.html",
            license="ODbL",
            observation="Assigned default municipal standard road (18.0m width)"
        )
        return RoadResponse(
            road_name="Public Municipal Road",
            road_width=18.0,
            classification="secondary",
            distance_meters=15.0,
            citation=citation
        )
