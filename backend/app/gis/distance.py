"""
GIS Spatial Distance Calculator
==============================
Provides high-accuracy geodesic and projected distance algorithms for
road proximity, lake buffer detection, and storm drain clearances.
"""

import math
from shapely.geometry import Point
from shapely.geometry.base import BaseGeometry
from app.gis.geometry import latlon_to_mercator, project_geometry_to_meters


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate great-circle distance between two WGS84 points in meters.
    """
    r = 6371000.0  # Earth mean radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def calculate_spatial_distance_meters(
    point_or_geom: BaseGeometry,
    target_geom: BaseGeometry,
    source_lat: float,
    source_lon: float
) -> float:
    """
    Calculate Euclidean distance in meters between two geometries by projecting
    both to EPSG:3857 spherical mercator coordinates.
    """
    if point_or_geom is None or target_geom is None or target_geom.is_empty:
        return float('inf')

    # Convert point/geom to metric projection
    proj_src = project_geometry_to_meters(point_or_geom)
    proj_tgt = project_geometry_to_meters(target_geom)

    dist_mercator = proj_src.distance(proj_tgt)

    # Scale mercator distance to true geodesic distance at target latitude
    scale_factor = math.cos(math.radians(source_lat))
    true_distance_meters = dist_mercator * scale_factor
    return round(true_distance_meters, 2)
