"""
GIS Context Intelligence Schemas
================================
Pydantic v2 schemas for GIS Context inputs, outputs, dataset metadata, and citations.
"""

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class PointGeometry(BaseModel):
    """Latitude/Longitude point location."""
    latitude: float = Field(..., ge=-90.0, le=90.0, description="WGS84 Latitude")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="WGS84 Longitude")


class GISContextRequest(BaseModel):
    """Request payload for full urban context evaluation."""
    latitude: float = Field(..., ge=-90.0, le=90.0, json_schema_extra={"example": 12.9250})
    longitude: float = Field(..., ge=-180.0, le=180.0, json_schema_extra={"example": 77.5938})
    building_footprint: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional GeoJSON Polygon geometry representing building footprint"
    )


class CitationSchema(BaseModel):
    """Auditable citation for GIS datasets."""
    dataset_name: str
    authority: str
    source_url: str
    license: str
    feature_id: Optional[str] = None
    observation: str


class WardResponse(BaseModel):
    city: str = "Bangalore"
    authority: str = "BBMP"
    ward_name: str
    ward_number: Optional[int] = None
    is_inside_bbmp: bool = True
    citation: Optional[CitationSchema] = None


class ZoneResponse(BaseModel):
    city: str = "Bangalore"
    authority: str = "BBMP"
    zone: str
    ward: str
    ward_number: Optional[int] = None
    citation: Optional[CitationSchema] = None


class RoadResponse(BaseModel):
    road_name: str
    road_width: float = Field(..., description="Estimated/Recorded road width in meters")
    classification: str
    distance_meters: float
    citation: Optional[CitationSchema] = None


class LakeResponse(BaseModel):
    nearest_lake_name: str
    lake_distance: float = Field(..., description="Distance to nearest lake boundary in meters")
    lake_buffer: bool = Field(..., description="True if within 30m or 75m lake buffer zone")
    storm_drain_distance: float = Field(..., description="Distance to nearest storm drain/canal in meters")
    citation: Optional[CitationSchema] = None


class AirportResponse(BaseModel):
    airport_zone: bool = Field(..., description="True if inside airport height restriction zone")
    airport_height_limit: Optional[float] = Field(default=None, description="Max permitted height in meters AMSL/AGL if restricted")
    nearest_airport_name: Optional[str] = None
    citation: Optional[CitationSchema] = None


class FloodResponse(BaseModel):
    flood_risk: str = Field(..., description="Low, Medium, or High flood risk classification")
    proximity_to_drain_meters: float
    citation: Optional[CitationSchema] = None


class LandUseResponse(BaseModel):
    land_use: str = Field(..., description="Zoning land use classification (e.g., Residential, Commercial)")
    master_plan_zone: str
    citation: Optional[CitationSchema] = None


class GISContextResponse(BaseModel):
    """Full urban context evaluation output payload."""
    city: str = "Bangalore"
    authority: str = "BBMP"
    zone: str
    ward: str
    ward_number: Optional[int] = None
    road_name: str
    road_width: float
    land_use: str
    lake_distance: float
    lake_buffer: bool
    airport_zone: bool
    airport_height_limit: Optional[float] = None
    flood_risk: str
    heritage_zone: bool = False
    storm_drain_distance: float
    is_inside_bbmp: bool = True
    approval_report_text: str
    citations: List[CitationSchema] = Field(default_factory=list)
    execution_time_ms: float
