"""
GIS Spatial Index Module
========================
High-performance STRtree spatial index wrapper using Shapely 2.0 C-accelerated
structures. Eliminates O(N) linear scans for point-in-polygon and nearest-neighbor queries.
"""

from typing import List, Optional, Tuple, Dict, Any
from shapely.geometry import Point
from shapely.geometry.base import BaseGeometry
from shapely.strtree import STRtree
from app.gis.models import GISFeature


class SpatialIndex:
    """
    R-Tree / STRtree Spatial Index container for a specific dataset category.
    """

    def __init__(self, dataset_name: str, features: List[GISFeature]):
        self.dataset_name = dataset_name
        self.features = features
        self.geometries: List[BaseGeometry] = [f.geometry for f in features]
        
        if self.geometries:
            self._strtree: Optional[STRtree] = STRtree(self.geometries)
        else:
            self._strtree = None

    def query_point_in_polygon(self, point: Point) -> Optional[GISFeature]:
        """
        Find the first polygon feature containing the given Point.
        Uses STRtree bounding box filtering followed by exact contains check.
        """
        if self._strtree is None or not self.features:
            return None

        # STRtree query returns indices of geometries whose bounding box intersects point
        candidate_indices = self._strtree.query(point, predicate="intersects")
        
        for idx in candidate_indices:
            feat = self.features[idx]
            if feat.geometry.contains(point) or feat.geometry.intersects(point):
                return feat
                
        return None

    def query_nearest_feature(self, point: Point) -> Tuple[Optional[GISFeature], float]:
        """
        Find the nearest feature to the given Point and calculate index position.
        Returns (GISFeature, distance_degrees).
        """
        if self._strtree is None or not self.features:
            return None, float('inf')

        nearest_idx = self._strtree.nearest(point)
        if nearest_idx is None:
            return None, float('inf')
            
        feat = self.features[nearest_idx]
        dist_deg = point.distance(feat.geometry)
        return feat, dist_deg

    def query_bounding_box(self, min_x: float, min_y: float, max_x: float, max_y: float) -> List[GISFeature]:
        """Query features intersecting a given bounding box."""
        if self._strtree is None or not self.features:
            return []

        bbox_point_or_poly = Point(min_x, min_y).buffer(max(max_x - min_x, max_y - min_y))
        candidate_indices = self._strtree.query(bbox_point_or_poly)
        return [self.features[idx] for idx in candidate_indices]
