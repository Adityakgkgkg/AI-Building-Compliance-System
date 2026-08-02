"""
GIS Spatial Geometry Utilities
==============================
Provides robust geometric transformations, validation, GeoJSON parsing,
and CRS conversion functions for spatial processing.
"""

import math
from typing import Dict, Any, Tuple, Optional
from shapely.geometry import shape, Point, Polygon, MultiPolygon, LineString
from shapely.geometry.base import BaseGeometry
from shapely.validation import make_valid


def geojson_to_shapely(geojson_dict: Dict[str, Any]) -> BaseGeometry:
    """Convert a GeoJSON geometry dictionary or feature into a Shapely geometry object."""
    if "geometry" in geojson_dict and isinstance(geojson_dict["geometry"], dict):
        geom_dict = geojson_dict["geometry"]
    else:
        geom_dict = geojson_dict
    
    geom = shape(geom_dict)
    if not geom.is_valid:
        geom = make_valid(geom)
    return geom


def repair_geometry(geom: BaseGeometry) -> BaseGeometry:
    """Ensure a Shapely geometry is valid, applying repair if necessary."""
    if geom is None or geom.is_empty:
        return geom
    if not geom.is_valid:
        geom = make_valid(geom)
        if not geom.is_valid:
            # Fallback zero-distance buffer trick for polygon self-intersections
            geom = geom.buffer(0)
    return geom


def latlon_to_mercator(lat: float, lon: float) -> Tuple[float, float]:
    """
    Project WGS84 (EPSG:4326) Latitude/Longitude into EPSG:3857 (Spherical Mercator)
    coordinates in meters for accurate Euclidean spatial distance calculations.
    """
    r = 6378137.0  # WGS84 Equatorial radius in meters
    x = r * math.radians(lon)
    # Clip latitude to avoid infinity near poles
    clipped_lat = max(min(lat, 89.5), -89.5)
    y = r * math.log(math.tan(math.pi / 4.0 + math.radians(clipped_lat) / 2.0))
    return x, y


def project_geometry_to_meters(geom: BaseGeometry) -> BaseGeometry:
    """
    Transform a Shapely geometry in EPSG:4326 (lon, lat) into EPSG:3857 (x, y in meters).
    """
    if geom is None or geom.is_empty:
        return geom

    def transform_coords(coords):
        res = []
        for c in coords:
            lon, lat = c[0], c[1]
            x, y = latlon_to_mercator(lat, lon)
            res.append((x, y))
        return res

    if geom.geom_type == 'Point':
        x, y = latlon_to_mercator(geom.y, geom.x)
        return Point(x, y)
    elif geom.geom_type == 'LineString':
        return LineString(transform_coords(geom.coords))
    elif geom.geom_type == 'Polygon':
        shell = transform_coords(geom.exterior.coords)
        holes = [transform_coords(h.coords) for h in geom.interiors]
        return Polygon(shell, holes)
    elif geom.geom_type in ('MultiPolygon', 'MultiLineString'):
        sub_geoms = [project_geometry_to_meters(g) for g in geom.geoms]
        if geom.geom_type == 'MultiPolygon':
            return MultiPolygon(sub_geoms)
    return geom
