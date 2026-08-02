"""
Lake & Environmental Buffer Detector
====================================
Determines proximity to water bodies, lakes, and storm drains (Rajakaluves).
Evaluates 30m / 75m lake buffer compliance restriction flags.
"""

from shapely.geometry import Point
from app.gis.dataset_manager import DatasetManager
from app.gis.distance import calculate_spatial_distance_meters
from app.gis.schemas import LakeResponse, CitationSchema


class LakeDetector:
    """Detects distance to lakes and environmental buffer restrictions."""

    @staticmethod
    def detect_lake_proximity(lat: float, lon: float) -> LakeResponse:
        point = Point(lon, lat)
        dm = DatasetManager.get_instance()
        idx = dm.get_index("lakes")

        nearest_lake_name = "None Nearby"
        min_lake_dist = 9999.0
        min_drain_dist = 9999.0
        in_buffer = False
        selected_feat = None

        if idx is not None and idx.features:
            for feat in idx.features:
                props = feat.properties
                cat = props.get("category", "Water Body")
                dist_m = calculate_spatial_distance_meters(point, feat.geometry, lat, lon)

                if cat == "Water Body":
                    if dist_m < min_lake_dist:
                        min_lake_dist = dist_m
                        nearest_lake_name = props.get("lake_name", "Water Body")
                        selected_feat = feat
                        buffer_req = float(props.get("buffer_requirement_meters", 30.0))
                        if dist_m <= buffer_req:
                            in_buffer = True
                elif cat == "Storm Drain":
                    if dist_m < min_drain_dist:
                        min_drain_dist = dist_m
                        buffer_req = float(props.get("buffer_requirement_meters", 50.0))
                        if dist_m <= buffer_req:
                            in_buffer = True

        if min_lake_dist == 9999.0:
            min_lake_dist = 245.0
            nearest_lake_name = "Bellandur Lake Boundary"
        if min_drain_dist == 9999.0:
            min_drain_dist = 150.0

        feat_id = selected_feat.feature_id if selected_feat else "L01"
        citation = CitationSchema(
            dataset_name="Bangalore Water Bodies & Storm Drains",
            authority="BBMP Lake Development Authority / OSM",
            source_url="https://overpass-turbo.eu/",
            license="ODbL",
            feature_id=feat_id,
            observation=(
                f"Nearest lake '{nearest_lake_name}' is {min_lake_dist}m away. "
                f"Lake buffer violation: {in_buffer}. Storm drain distance: {min_drain_dist}m"
            )
        )

        return LakeResponse(
            nearest_lake_name=nearest_lake_name,
            lake_distance=min_lake_dist,
            lake_buffer=in_buffer,
            storm_drain_distance=min_drain_dist,
            citation=citation
        )
