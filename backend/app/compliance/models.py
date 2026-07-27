"""
AI Building Compliance System — Compliance Engine ORM Models

SQLAlchemy ORM model for persisting ComplianceReport records.

Design:
  - The report JSON is stored as a serialized blob to keep the schema
    flexible across rule-set versions without requiring migrations.
  - Future sprints can add a FK to IFCFileRecord when a shared DB layer
    is introduced.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ComplianceReportRecord(Base):
    """
    Persisted compliance check result.

    Stores the full ComplianceReport JSON alongside key scalar fields
    for fast querying (status, score, file_id) without requiring JSON
    parsing on every lookup.

    Table: compliance_reports
    """

    __tablename__ = "compliance_reports"

    # ── Primary key ──────────────────────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # ── Traceability ─────────────────────────────────────────────
    report_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True,
        nullable=False,
        comment="UUID4 identifying this specific compliance run.",
    )
    file_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        index=True,
        nullable=True,
        comment="IFC file UUID from the parser (nullable if parse_result supplied inline).",
    )

    # ── Rule set ─────────────────────────────────────────────────
    rules_file: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        default="bbmp_2003_residential",
        comment="Name of the rules JSON file used for this check.",
    )
    authority: Mapped[str] = mapped_column(
        String(64), nullable=False, default="BBMP"
    )
    bye_laws: Mapped[str] = mapped_column(
        String(32), nullable=False, default="2003"
    )

    # ── Scalar results (indexed for fast querying) ────────────────
    overall_status: Mapped[str] = mapped_column(String(32), nullable=False)
    compliance_score: Mapped[int] = mapped_column(Integer, nullable=False)
    total_rules: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    passed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # ── Full report blob ─────────────────────────────────────────
    report_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Full ComplianceReport serialized as JSON string.",
    )

    # ── Timestamps ───────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ── Helpers ──────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """Return a lightweight dict summary (without full JSON blob)."""
        return {
            "report_id": self.report_id,
            "file_id": self.file_id,
            "overall_status": self.overall_status,
            "compliance_score": self.compliance_score,
            "total_rules": self.total_rules,
            "passed": self.passed_count,
            "failed": self.failed_count,
            "warnings": self.warning_count,
            "rules_file": self.rules_file,
            "authority": self.authority,
            "bye_laws": self.bye_laws,
            "created_at": self.created_at.isoformat(),
        }

    def get_report(self) -> Dict[str, Any]:
        """Deserialize and return the full ComplianceReport dict."""
        return json.loads(self.report_json)

    def __repr__(self) -> str:
        return (
            f"ComplianceReportRecord("
            f"report_id={self.report_id!r}, "
            f"file_id={self.file_id!r}, "
            f"status={self.overall_status!r}, "
            f"score={self.compliance_score})"
        )
