"""
GIS Context Intelligence Domain Models
=======================================
Internal domain representations of spatial datasets and metadata.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from shapely.geometry.base import BaseGeometry


@dataclass
class GISFeature:
    """Represents a spatial feature extracted from a dataset."""
    feature_id: str
    geometry: BaseGeometry
    properties: Dict[str, Any]
    dataset_name: str


@dataclass
class DatasetMetadata:
    """Metadata describing an approved GIS dataset."""
    dataset_name: str
    file_name: str
    source_url: str
    authority: str
    license: str
    download_date: str
    last_updated: str
    coordinate_system: str = "EPSG:4326"
    version: str = "1.0"
    checksum_sha256: str = ""
    geometry_count: int = 0
    status: str = "VERIFIED"


@dataclass
class SpatialQueryResult:
    """Container for spatial lookup operations."""
    feature: Optional[GISFeature]
    distance_meters: float = 0.0
    is_intersecting: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
