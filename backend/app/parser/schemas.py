"""
MCRDSE Module 1 – IFC Parser Engine Schemas
===========================================
Pydantic v2 strict models defining the canonical parsed outputs, metadata,
geometry, storeys, spaces, elements, and statistics schemas.

Design rules:
- Strict Pydantic v2 models (`model_config = ConfigDict(strict=True, frozen=True)`).
- No `Any` types allowed.
- ``ParsedBuildingResult`` attributes map 1-to-1 with ``EvidenceCollector.collect_building()``.
- Preserves native IFC GlobalId for all entities to support future 3D visualization.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

_STRICT = ConfigDict(strict=True, frozen=True)


class ParsedBuildingResult(BaseModel):
    """
    Attribute-compatible object returned by ``IFCParserService.parse()``.
    Matches the exact interface expected by ``EvidenceCollector.collect_building()``.
    """

    model_config = _STRICT

    building_id: str = Field(..., description="Unique building GlobalId or UUID.")
    building_name: str = Field(..., description="Human-readable building name.")
    building_type: str = Field(..., description="Building classification string (e.g. 'RESIDENTIAL').")
    plot_area: float = Field(..., ge=0.0, description="Plot area in square metres.")
    builtup_area: float = Field(..., ge=0.0, description="Total built-up area across all floors in m².")
    height: float = Field(..., ge=0.0, description="Building height in metres.")
    floors: int = Field(..., ge=0, description="Total number of floors above ground.")
    fsi: float = Field(..., ge=0.0, description="Floor Space Index = builtup_area / plot_area.")
    ground_coverage: float = Field(..., ge=0.0, le=100.0, description="Ground coverage percentage.")
    occupancy: str = Field(..., description="Occupancy type string.")


class IFCMetadata(BaseModel):
    """Extracted building identity, project, site, and author metadata."""

    model_config = _STRICT

    global_id: str = Field(..., description="IFC GlobalId of the building.")
    building_name: str = Field(..., description="Name of the building.")
    project_name: str = Field(..., description="Name of the IFC project.")
    site_name: str = Field(..., description="Name of the IFC site.")
    building_type: str = Field(..., description="Building classification/type.")
    occupancy: str = Field(..., description="Occupancy classification.")
    description: Optional[str] = Field(default=None, description="Building description.")
    long_name: Optional[str] = Field(default=None, description="Building long name.")
    schema_version: str = Field(..., description="IFC schema version ('IFC2X3', 'IFC4', 'IFC4X3').")
    author: str = Field(..., description="Author of the IFC file.")
    organization: str = Field(..., description="Organization originating the file.")
    timestamp: str = Field(..., description="Creation timestamp recorded in the IFC header.")
    application: str = Field(..., description="BIM authoring software tool (e.g. Revit, ArchiCAD).")
    owner_history: Optional[str] = Field(default=None, description="Owner history string.")


class IFCBoundingBox(BaseModel):
    """Axis-aligned 3D bounding box coordinates and dimensions."""

    model_config = _STRICT

    min_x: float = Field(..., description="Minimum X coordinate (m).")
    min_y: float = Field(..., description="Minimum Y coordinate (m).")
    min_z: float = Field(..., description="Minimum Z coordinate (m).")
    max_x: float = Field(..., description="Maximum X coordinate (m).")
    max_y: float = Field(..., description="Maximum Y coordinate (m).")
    max_z: float = Field(..., description="Maximum Z coordinate (m).")
    width: float = Field(..., ge=0.0, description="Building width along X axis (m).")
    length: float = Field(..., ge=0.0, description="Building length along Y axis (m).")
    height: float = Field(..., ge=0.0, description="Building height along Z axis (m).")
    centroid_x: float = Field(..., description="Centroid X coordinate (m).")
    centroid_y: float = Field(..., description="Centroid Y coordinate (m).")
    centroid_z: float = Field(..., description="Centroid Z coordinate (m).")


class IFCGeometry(BaseModel):
    """Geometric extraction payload."""

    model_config = _STRICT

    bounding_box: IFCBoundingBox = Field(..., description="3D axis-aligned bounding box.")
    building_length: float = Field(..., ge=0.0, description="Length in metres.")
    building_width: float = Field(..., ge=0.0, description="Width in metres.")
    building_height: float = Field(..., ge=0.0, description="Overall height in metres.")
    ground_elevation: float = Field(..., description="Ground elevation relative to datum (m).")
    roof_elevation: float = Field(..., description="Roof elevation relative to datum (m).")


class IFCStorey(BaseModel):
    """Extracted building storey record preserving IFC GlobalId."""

    model_config = _STRICT

    global_id: str = Field(..., description="IFC GlobalId of the IfcBuildingStorey.")
    name: str = Field(..., description="Storey name (e.g. 'Level 1', 'Ground Floor').")
    elevation: float = Field(..., description="Elevation above datum (m).")
    height: float = Field(..., ge=0.0, description="Floor-to-floor height (m).")
    area: float = Field(..., ge=0.0, description="Gross slab/storey area (m²).")
    rooms_count: int = Field(..., ge=0, description="Number of spaces/rooms on this storey.")
    walls_count: int = Field(..., ge=0, description="Number of walls on this storey.")


class IFCSpace(BaseModel):
    """Extracted space/room record preserving IFC GlobalId."""

    model_config = _STRICT

    global_id: str = Field(..., description="IFC GlobalId of the IfcSpace.")
    name: str = Field(..., description="Space/room name.")
    long_name: Optional[str] = Field(default=None, description="Space long name.")
    usage: str = Field(..., description="Space usage/function string.")
    area: float = Field(..., ge=0.0, description="Net floor area in m².")
    volume: float = Field(..., ge=0.0, description="Net room volume in m³.")
    storey_name: str = Field(..., description="Name of the containing storey.")
    storey_global_id: Optional[str] = Field(default=None, description="GlobalId of the containing storey.")


class IFCElementCount(BaseModel):
    """Entity count summary for 17 major IFC element types."""

    model_config = _STRICT

    walls: int = Field(..., ge=0, description="IfcWall + IfcWallStandardCase count.")
    doors: int = Field(..., ge=0, description="IfcDoor count.")
    windows: int = Field(..., ge=0, description="IfcWindow count.")
    columns: int = Field(..., ge=0, description="IfcColumn count.")
    beams: int = Field(..., ge=0, description="IfcBeam count.")
    slabs: int = Field(..., ge=0, description="IfcSlab count.")
    roofs: int = Field(..., ge=0, description="IfcRoof count.")
    footings: int = Field(..., ge=0, description="IfcFooting count.")
    stairs: int = Field(..., ge=0, description="IfcStair count.")
    ramps: int = Field(..., ge=0, description="IfcRamp count.")
    spaces: int = Field(..., ge=0, description="IfcSpace count.")
    storeys: int = Field(..., ge=0, description="IfcBuildingStorey count.")
    openings: int = Field(..., ge=0, description="IfcOpeningElement count.")
    curtain_walls: int = Field(..., ge=0, description="IfcCurtainWall count.")
    coverings: int = Field(..., ge=0, description="IfcCovering count.")
    railings: int = Field(..., ge=0, description="IfcRailing count.")
    total: int = Field(..., ge=0, description="Total count of all major elements.")


class IFCStatistics(BaseModel):
    """Aggregated building statistics payload."""

    model_config = _STRICT

    floors: int = Field(..., ge=0, description="Number of floors above ground.")
    basements: int = Field(..., ge=0, description="Number of basement levels.")
    elements: IFCElementCount = Field(..., description="Detailed element count breakdown.")
    gross_floor_area: float = Field(..., ge=0.0, description="Gross floor area across all storeys (m²).")
    net_floor_area: float = Field(..., ge=0.0, description="Sum of net space areas (m²).")
    builtup_area: float = Field(..., ge=0.0, description="Total built-up area in m².")
    ground_coverage: float = Field(..., ge=0.0, le=100.0, description="Ground coverage percentage.")
    plot_area: float = Field(..., ge=0.0, description="Site/plot area in m².")
    fsi: float = Field(..., ge=0.0, description="Floor Space Index.")


class IFCParseSummary(BaseModel):
    """Full parsing payload returned by detailed endpoints."""

    model_config = ConfigDict(strict=True, frozen=True)

    file_name: str = Field(..., description="Uploaded IFC file name.")
    parse_id: str = Field(..., description="UUID4 identifier for this parse operation.")
    parsed_at: datetime = Field(..., description="UTC timestamp of completion.")
    execution_time_ms: float = Field(..., ge=0.0, description="Total wall-clock execution time in ms.")
    building_evidence: ParsedBuildingResult = Field(..., description="Canonical building evidence payload.")
    metadata: IFCMetadata = Field(..., description="Detailed IFC metadata.")
    geometry: IFCGeometry = Field(..., description="Detailed 3D geometry.")
    storeys: List[IFCStorey] = Field(default_factory=list, description="Extracted storeys list.")
    spaces: List[IFCSpace] = Field(default_factory=list, description="Extracted spaces list.")
    statistics: IFCStatistics = Field(..., description="Aggregated statistics payload.")


class IFCHealthStatus(BaseModel):
    """Health status payload for parser engine."""

    model_config = _STRICT

    status: str = Field(..., description="Engine status ('healthy' or 'degraded').")
    ifcopenshell_version: str = Field(..., description="IfcOpenShell version.")
    supported_schemas: List[str] = Field(..., description="Supported IFC schema list.")
