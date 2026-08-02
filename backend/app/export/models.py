"""
MCRDSE Sprint 4 – Report Audit Trail Persistence Model
======================================================
SQLAlchemy ORM model recording report generation events, SHA256 checksums,
verdicts, and stored file paths for audit verification.
"""

from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ReportAuditRecord(Base):
    """
    SQLAlchemy ORM model for report generation audit trail.
    """

    __tablename__ = "report_audit_records"

    report_id = Column(String(36), primary_key=True, index=True)
    ifc_file = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    checksum_sha256 = Column(String(64), nullable=False, index=True)
    sanction_verdict = Column(String(255), nullable=False)
    readiness_score = Column(Float, nullable=False)
    authority = Column(String(100), nullable=False)
    ward = Column(String(100), nullable=False)
    pdf_path = Column(Text, nullable=True)
    html_path = Column(Text, nullable=True)
    json_path = Column(Text, nullable=True)
    software_version = Column(String(50), nullable=False)
