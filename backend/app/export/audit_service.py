"""
MCRDSE Sprint 4 – Audit Trail & Report Storage Service
======================================================
Handles persistent storage of generated PDF/HTML/JSON report files, SHA256 integrity
checksum calculations, and database audit record persistence.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from app.export.models import ReportAuditRecord
from app.export.schemas import AuditRecordSchema, ReportData

logger = logging.getLogger("app.export.audit_service")

_REPORTS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "reports"


class AuditTrailService:
    """
    Service managing report file storage, SHA256 hashing, and audit log persistence.
    """

    # In-memory store for fast retrieval across requests in a session
    _memory_cache: Dict[str, dict] = {}

    @classmethod
    def initialize_storage(cls) -> None:
        """Ensure reports directory exists."""
        _REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def save_report(
        cls,
        report_data: ReportData,
        pdf_bytes: bytes,
        html_str: str,
        json_str: str,
        host_base_url: str = "http://localhost:8000",
        db: Optional[object] = None,
    ) -> AuditRecordSchema:
        """
        Save report files to disk and record audit log.
        """
        cls.initialize_storage()
        report_id = report_data.report_id
        ctx = report_data.decision_context

        # File paths
        pdf_path = _REPORTS_DIR / f"{report_id}.pdf"
        html_path = _REPORTS_DIR / f"{report_id}.html"
        json_path = _REPORTS_DIR / f"{report_id}.json"

        # Write files
        pdf_path.write_bytes(pdf_bytes)
        html_path.write_text(html_str, encoding="utf-8")
        json_path.write_text(json_str, encoding="utf-8")

        verification_url = f"{host_base_url}/api/v1/export/status/{report_id}?checksum={report_data.checksum_sha256[:16]}"

        audit_record = AuditRecordSchema(
            report_id=report_id,
            ifc_file=ctx.evidence_bundle.building.ifc_file,
            created_at=report_data.generated_at,
            checksum_sha256=report_data.checksum_sha256,
            sanction_verdict=ctx.approval.sanction_verdict,
            readiness_score=ctx.approval.readiness_score,
            authority=ctx.evidence_bundle.gis.authority,
            verification_url=verification_url,
        )

        # Cache in memory
        cls._memory_cache[report_id] = {
            "report_data": report_data,
            "pdf_bytes": pdf_bytes,
            "html_str": html_str,
            "json_str": json_str,
            "audit_record": audit_record,
            "pdf_path": str(pdf_path),
            "html_path": str(html_path),
            "json_path": str(json_path),
        }

        # Persist to DB if session provided
        if db is not None:
            try:
                rec = ReportAuditRecord(
                    report_id=report_id,
                    ifc_file=ctx.evidence_bundle.building.ifc_file,
                    created_at=report_data.generated_at,
                    checksum_sha256=report_data.checksum_sha256,
                    sanction_verdict=ctx.approval.sanction_verdict,
                    readiness_score=ctx.approval.readiness_score,
                    authority=ctx.evidence_bundle.gis.authority,
                    ward=ctx.evidence_bundle.gis.ward,
                    pdf_path=str(pdf_path),
                    html_path=str(html_path),
                    json_path=str(json_path),
                    software_version=ctx.evidence_bundle.software_version,
                )
                db.add(rec)  # type: ignore[union-attr]
                db.commit()  # type: ignore[union-attr]
                logger.info("ReportAuditRecord persisted to DB | report_id=%s", report_id)
            except Exception as exc:
                logger.error("Failed to persist ReportAuditRecord | error=%s", exc)

        return audit_record

    @classmethod
    def get_pdf_bytes(cls, report_id: str) -> Optional[bytes]:
        """Retrieve PDF bytes for a report ID."""
        if report_id in cls._memory_cache:
            return cls._memory_cache[report_id]["pdf_bytes"]

        pdf_path = _REPORTS_DIR / f"{report_id}.pdf"
        if pdf_path.exists():
            return pdf_path.read_bytes()

        return None

    @classmethod
    def get_html_str(cls, report_id: str) -> Optional[str]:
        """Retrieve HTML string for a report ID."""
        if report_id in cls._memory_cache:
            return cls._memory_cache[report_id]["html_str"]

        html_path = _REPORTS_DIR / f"{report_id}.html"
        if html_path.exists():
            return html_path.read_text(encoding="utf-8")

        return None

    @classmethod
    def get_json_dict(cls, report_id: str) -> Optional[dict]:
        """Retrieve JSON dictionary for a report ID."""
        if report_id in cls._memory_cache:
            rd: ReportData = cls._memory_cache[report_id]["report_data"]
            return rd.model_dump(mode="json")

        json_path = _REPORTS_DIR / f"{report_id}.json"
        if json_path.exists():
            return json.loads(json_path.read_text(encoding="utf-8"))

        return None

    @classmethod
    def get_audit_record(cls, report_id: str) -> Optional[AuditRecordSchema]:
        """Retrieve audit record for a report ID."""
        if report_id in cls._memory_cache:
            return cls._memory_cache[report_id]["audit_record"]

        json_dict = cls.get_json_dict(report_id)
        if json_dict and "decision_context" in json_dict:
            ctx = json_dict["decision_context"]
            return AuditRecordSchema(
                report_id=report_id,
                ifc_file=ctx["evidence_bundle"]["building"]["ifc_file"],
                created_at=datetime.fromisoformat(json_dict["generated_at"]),
                checksum_sha256=json_dict["checksum_sha256"],
                sanction_verdict=ctx["approval"]["sanction_verdict"],
                readiness_score=ctx["approval"]["readiness_score"],
                authority=ctx["evidence_bundle"]["gis"]["authority"],
                verification_url=f"http://localhost:8000/api/v1/export/status/{report_id}",
            )

        return None
