"""
AI Building Compliance System — IFC Parser Schemas

Pydantic v2 request/response models for the parser module.

These schemas form the stable JSON contract that future modules
(compliance engine, GIS, AI) will consume. Do not remove fields;
add new optional fields in future sprints to stay backward-compatible.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


# ── Upload ────────────────────────────────────────────────────────

class UploadIFCResponse(BaseModel):
    """Response returned after a successful IFC file upload."""

    file_id: str = Field(
        ...,
        description="Unique identifier for the uploaded file (UUID4).",
        examples=["3f7e2a1b-9c4d-4e8f-b0a2-123456789abc"],
    )
    filename: str = Field(
        ...,
        description="Original filename as submitted by the client.",
        examples=["building_plan.ifc"],
    )
    status: str = Field(
        default="uploaded",
        description="Upload status. Always 'uploaded' on success.",
        examples=["uploaded"],
    )


# ── Building Information ──────────────────────────────────────────

class BuildingInfo(BaseModel):
    """Extracted metadata from IfcProject, IfcBuilding, and IfcSite."""

    project_name: Optional[str] = Field(
        None,
        description="Name from IfcProject.",
        examples=["Commercial Tower A"],
    )
    building_name: Optional[str] = Field(
        None,
        description="Name from IfcBuilding.",
        examples=["Tower Block 1"],
    )
    site_name: Optional[str] = Field(
        None,
        description="Name from IfcSite.",
        examples=["Plot 42, Business District"],
    )
    description: Optional[str] = Field(
        None,
        description="Description from IfcBuilding.",
        examples=["Mixed-use commercial tower"],
    )
    ifc_schema: Optional[str] = Field(
        None,
        description="IFC schema version string (e.g. IFC4, IFC2X3).",
        examples=["IFC4", "IFC2X3"],
    )
    storeys: int = Field(
        default=0,
        description="Number of IfcBuildingStorey entities found.",
        examples=[3],
    )
    units: Optional[str] = Field(
        None,
        description="Primary length unit from IfcUnitAssignment.",
        examples=["METRE", "MILLIMETRE"],
    )
    owner: Optional[str] = Field(
        None,
        description="Organization name from IfcOwnerHistory.",
        examples=["ACME Architecture Firm"],
    )


# ── Element Counts ────────────────────────────────────────────────

class ElementCounts(BaseModel):
    """Count of IFC building elements by type."""

    walls: int = Field(default=0, description="Number of IfcWall entities.", examples=[42])
    doors: int = Field(default=0, description="Number of IfcDoor entities.", examples=[15])
    windows: int = Field(default=0, description="Number of IfcWindow entities.", examples=[18])
    slabs: int = Field(default=0, description="Number of IfcSlab entities.", examples=[4])
    columns: int = Field(default=0, description="Number of IfcColumn entities.", examples=[12])
    beams: int = Field(default=0, description="Number of IfcBeam entities.", examples=[20])
    roofs: int = Field(default=0, description="Number of IfcRoof entities.", examples=[1])
    stairs: int = Field(default=0, description="Number of IfcStair entities.", examples=[2])
    spaces: int = Field(default=0, description="Number of IfcSpace entities.", examples=[10])
    openings: int = Field(
        default=0,
        description="Number of IfcOpeningElement entities.",
        examples=[5],
    )


# ── Geometry Information ──────────────────────────────────────────

class GeometryInfo(BaseModel):
    """
    Best-effort geometric properties of the building.

    All fields are Optional — if geometry cannot be computed from
    the IFC file (e.g. no 3D geometry present), they are null.
    Never raises an exception; returns null instead.
    """

    gross_floor_area: Optional[float] = Field(
        None,
        description="Gross floor area in square metres (if available).",
        examples=[1250.0],
    )
    height: Optional[float] = Field(
        None,
        description="Total building height in metres (if available).",
        examples=[12.5],
    )
    storey_heights: Optional[list[float]] = Field(
        None,
        description="Height of each storey in metres, bottom to top.",
        examples=[[3.5, 3.5, 3.0]],
    )
    footprint: Optional[float] = Field(
        None,
        description="Ground floor footprint area in square metres.",
        examples=[450.0],
    )
    bounding_box: Optional[dict] = Field(
        None,
        description="Axis-aligned bounding box: {min_x, min_y, min_z, max_x, max_y, max_z}.",
        examples=[{"min_x": 0.0, "min_y": 0.0, "min_z": 0.0,
                   "max_x": 30.0, "max_y": 20.0, "max_z": 12.5}],
    )


# ── Parse Result (Stable Contract) ───────────────────────────────

class ParseResult(BaseModel):
    """
    Canonical output of the IFC Parser.

    This is the stable JSON contract consumed by all future modules:
      - Sprint 3: Compliance engine reads building + elements
      - Sprint 4: GIS integration reads geometry
      - Sprint 5: AI recommendations read all three sections

    Do NOT remove or rename existing fields. Add new optional fields only.
    """

    building: BuildingInfo = Field(..., description="Extracted building metadata.")
    elements: ElementCounts = Field(..., description="Extracted element counts.")
    geometry: GeometryInfo = Field(..., description="Extracted geometry information.")


# ── Status Response ───────────────────────────────────────────────

class ParseStatusResponse(BaseModel):
    """Returned when parse is triggered but result not yet available."""

    file_id: str = Field(..., description="File identifier.", examples=["3f7e2a1b-..."])
    status: str = Field(
        ...,
        description="Current status: uploaded | parsing | parsed | error",
        examples=["parsed"],
    )
    message: Optional[str] = Field(
        None,
        description="Human-readable detail (e.g. error reason).",
        examples=["File parsed successfully."],
    )


# ── Error Response ────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    """Standard error envelope returned for 4xx/5xx responses."""

    detail: str = Field(
        ...,
        description="Human-readable error message.",
        examples=["File not found for the given file_id."],
    )
