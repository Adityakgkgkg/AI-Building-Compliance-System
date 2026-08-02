"""
MCRDSE Sprint 4 – Export Engine Schemas
========================================
Pydantic v2 strict-typed data models defining the canonical schemas for export
requests, responses, audit records, and report structure.

Design rules:
- Strict Pydantic v2 models (`model_config = ConfigDict(strict=True, frozen=True)`).
- No `Any` types allowed.
- Every field maps deterministically from canonical EvidenceBundle and DecisionContext.
- Immutable and serialisable to JSON.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.decision.schemas import DecisionContext


_STRICT = ConfigDict(strict=True, frozen=True)


class ExportRequest(BaseModel):
    """
    Request parameters for report generation.
    """

    model_config = _STRICT

    ifc_file: str = Field(..., description="Filename of the uploaded IFC building plan.")
    lat: float = Field(..., ge=-90.0, le=90.0, description="WGS84 latitude of the site.")
    lon: float = Field(..., ge=-180.0, le=180.0, description="WGS84 longitude of the site.")
    formats: List[str] = Field(
        default_factory=lambda: ["pdf", "html", "json"],
        description="List of requested export formats ('pdf', 'html', 'json').",
    )


class AuditRecordSchema(BaseModel):
    """
    Audit log schema for report verification.
    """

    model_config = _STRICT

    report_id: str = Field(..., description="UUID4 report identifier.")
    ifc_file: str = Field(..., description="Filename of the IFC plan.")
    created_at: datetime = Field(..., description="UTC creation timestamp.")
    checksum_sha256: str = Field(..., description="SHA256 integrity hash.")
    sanction_verdict: str = Field(..., description="Official sanction verdict string.")
    readiness_score: float = Field(..., ge=0.0, le=100.0, description="Readiness score.")
    author: str = Field(default="MCRDSE Automated Compliance Engine", description="Report issuing authority.")
    authority: str = Field(..., description="Planning authority jurisdiction.")
    verification_url: str = Field(..., description="URL to verify report authenticity.")


class ExportResponse(BaseModel):
    """
    Response returned upon report generation.
    """

    model_config = _STRICT

    report_id: str = Field(..., description="UUID4 report identifier.")
    status: str = Field(..., description="Status string: 'COMPLETED' or 'FAILED'.")
    available_formats: List[str] = Field(..., description="List of generated export formats.")
    created_at: datetime = Field(..., description="UTC creation timestamp.")
    checksum_sha256: str = Field(..., description="SHA256 payload integrity hash.")
    audit_record: AuditRecordSchema = Field(..., description="Audit record details.")


class ReportSection(BaseModel):
    """
    Single section inside the structured report.
    """

    model_config = _STRICT

    section_id: str = Field(..., description="Section identifier (e.g. 'SEC-01-COVER').")
    title: str = Field(..., description="Section title.")
    content_summary: str = Field(..., description="Brief text content summary.")


class ReportData(BaseModel):
    """
    Unified canonical data object feeding PDF, HTML, and JSON generators.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    report_id: str = Field(..., description="UUID4 report identifier.")
    generated_at: datetime = Field(..., description="UTC generation timestamp.")
    decision_context: DecisionContext = Field(..., description="Full decision context payload.")
    qr_code_base64: str = Field(..., description="Base64 encoded PNG of the verification QR code.")
    checksum_sha256: str = Field(..., description="SHA256 payload checksum.")
    sections: List[ReportSection] = Field(default_factory=list, description="Ordered list of report sections.")
