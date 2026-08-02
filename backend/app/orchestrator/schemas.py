"""
MCRDSE Analysis Orchestrator – Schemas
======================================
Strict Pydantic v2 schemas defining orchestrator responses, stage updates,
and the unified analysis execution payload.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AnalysisProgressResponse(BaseModel):
    """Execution progress update response."""

    analysis_id: str = Field(..., description="UUID4 analysis identifier.")
    status: str = Field(..., description="Status: 'running', 'completed', 'failed'.")
    current_stage: str = Field(..., description="Current execution stage string.")
    progress: int = Field(..., ge=0, le=100, description="Completion percentage in [0, 100].")
    error: Optional[Dict[str, Any]] = Field(default=None, description="Error detail if status is failed.")


class UnifiedAnalysisResponse(BaseModel):
    """Canonical unified response returned by POST /api/v1/analyze."""

    analysis_id: str = Field(..., description="UUID4 analysis identifier.")
    status: str = Field(default="completed", description="Execution status.")
    current_stage: str = Field(default="Completed", description="Final stage description.")
    progress: int = Field(default=100, description="Final progress percentage (100).")
    
    # Sub-module output payloads
    building: Dict[str, Any] = Field(..., description="Building evidence from Module 1 IFC Parser.")
    classification: Dict[str, Any] = Field(..., description="Classification evidence from Module 2.")
    gis: Dict[str, Any] = Field(..., description="GIS spatial context evidence from Module 3.")
    compliance: Dict[str, Any] = Field(..., description="Compliance evaluation evidence from Module 2 Engine.")
    evidence: Dict[str, Any] = Field(..., description="Canonical EvidenceBundle payload.")
    decision: Dict[str, Any] = Field(..., description="Decision context and approval verdict from Decision Engine.")
    reports: Dict[str, Any] = Field(..., description="Export engine report generation details.")

    # Redirect and Timing
    dashboard_url: str = Field(..., description="URL to navigate to municipal compliance dashboard.")
    report_url: str = Field(..., description="URL to view/download PDF/HTML report.")
    processing_time: Dict[str, float] = Field(..., description="Per-module wall-clock execution breakdown (ms).")
    total_processing_time: float = Field(..., description="Total end-to-end processing time (ms).")
