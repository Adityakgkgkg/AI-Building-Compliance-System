"""
AI Building Compliance System — Pydantic Schemas

Request/response schemas for API validation and serialization.
"""

from datetime import datetime
from pydantic import BaseModel, Field


# ── Health ───────────────────────────────────────────────────────
class HealthResponse(BaseModel):
    """Response schema for the health check endpoint."""
    status: str = Field(default="running", examples=["running"])


# ── Upload ───────────────────────────────────────────────────────
class UploadResponse(BaseModel):
    """Response schema for file upload endpoint."""
    filename: str = Field(..., examples=["building_plan.ifc"])
    size: int = Field(..., description="File size in bytes", examples=[1048576])
    type: str = Field(..., description="File extension", examples=[".ifc"])
    upload_time: datetime = Field(..., description="UTC timestamp of upload")


# ── Future Schemas (Sprint 2+) ───────────────────────────────────
class BuildingInfo(BaseModel):
    """Placeholder — will hold parsed building metadata from IFC files."""
    pass


class ComplianceResult(BaseModel):
    """Placeholder — will hold compliance check results."""
    pass


class GISContext(BaseModel):
    """Placeholder — will hold GIS/geospatial context data."""
    pass


class AIRecommendation(BaseModel):
    """Placeholder — will hold AI-generated recommendations."""
    pass
