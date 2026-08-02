"""
MCRDSE Sprint 1 – ORM Persistence Model
========================================
SQLAlchemy ORM model for persisting serialised ``EvidenceBundle`` snapshots
to the application database for audit and traceability.

Scope:
- Defines the ``evidence_bundles`` table schema.
- Stores the full JSON payload of each ``EvidenceBundle`` collected.
- Does **not** re-derive or transform bundle data; it only archives it.

Persistence is opt-in from the service layer (``persist=True`` flag).
Sprint 1 does not mandate persistence; the model is wired for future sprints.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Local declarative base for the report module ORM models."""


class EvidenceBundleRecord(Base):
    """
    Persisted snapshot of a completed ``EvidenceBundle`` collection run.

    One row is created per successful (or partially successful) collection
    request.  The ``bundle_json`` column stores the full Pydantic-serialised
    JSON so that the exact state of all upstream module outputs at report-time
    is preserved for auditing.
    """

    __tablename__ = "evidence_bundles"

    # ── Primary key ──────────────────────────────────────────────────────────
    id: int = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # ── Identity ─────────────────────────────────────────────────────────────
    report_id: str = Column(
        String(36),
        unique=True,
        nullable=False,
        index=True,
        comment="UUID4 report identifier — maps to EvidenceBundle.report_id.",
    )

    # ── Source ───────────────────────────────────────────────────────────────
    ifc_file: str = Column(
        String(512),
        nullable=False,
        comment="Original IFC filename submitted for this compliance run.",
    )

    # ── Temporal ─────────────────────────────────────────────────────────────
    created_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="UTC timestamp when this record was inserted.",
    )

    # ── Payload ──────────────────────────────────────────────────────────────
    bundle_json: str = Column(
        Text,
        nullable=False,
        comment="Full JSON-serialised EvidenceBundle payload.",
    )

    # ── Summary metrics (indexed for fast dashboard queries) ─────────────────
    compliance_score: float = Column(
        Float,
        nullable=True,
        comment="Compliance score extracted from the bundle for quick lookups.",
    )
    blocking_violations: int = Column(
        Integer,
        nullable=True,
        comment="Count of BLOCKING violations from the compliance evidence.",
    )
    gis_ward: str = Column(
        String(256),
        nullable=True,
        comment="BBMP ward name extracted from GIS evidence for fast filtering.",
    )
    software_version: str = Column(
        String(32),
        nullable=True,
        comment="Application version at the time this bundle was collected.",
    )

    def __repr__(self) -> str:
        return (
            f"<EvidenceBundleRecord report_id={self.report_id!r} "
            f"ifc_file={self.ifc_file!r} "
            f"score={self.compliance_score}>"
        )
