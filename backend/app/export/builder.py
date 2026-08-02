"""
MCRDSE Sprint 4 – Report Builder
=================================
Assembles the canonical ``ReportData`` object combining ``DecisionContext`` with QR codes,
SHA256 checksums, and structured 10-section report index.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from app.decision.schemas import DecisionContext
from app.export.qr_generator import QRCodeGenerator
from app.export.schemas import ReportData, ReportSection


class ReportBuilder:
    """
    Builder assembling ReportData from canonical DecisionContext.
    """

    @staticmethod
    def build_report_data(context: DecisionContext, host_base_url: str = "http://localhost:8000") -> ReportData:
        """
        Build the ReportData canonical payload.

        Parameters
        ----------
        context:
            Canonical DecisionContext object.
        host_base_url:
            Base URL for verification link QR code.

        Returns
        -------
        ReportData
            Canonical report data object.
        """
        report_id = context.evidence_bundle.report_id

        # Calculate SHA256 payload checksum
        canonical_json = json.dumps(context.model_dump(mode="json"), sort_keys=True, ensure_ascii=False)
        checksum_sha256 = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

        # Verification URL
        verification_url = f"{host_base_url}/api/v1/export/status/{report_id}?checksum={checksum_sha256[:16]}"

        # Generate QR code
        _, qr_b64 = QRCodeGenerator.generate_qr_code(verification_url)

        # 10 Report Sections
        sections = [
            ReportSection(section_id="SEC-01-COVER", title="Cover Page", content_summary="Official Municipal Plan Sanction Audit Record"),
            ReportSection(section_id="SEC-02-EXEC", title="Executive Summary", content_summary=context.summary.sanction_recommendation),
            ReportSection(section_id="SEC-03-BUILDING", title="Building Summary", content_summary=f"IFC Building: {context.evidence_bundle.building.building_name}"),
            ReportSection(section_id="SEC-04-GIS", title="GIS Context", content_summary=f"Ward: {context.evidence_bundle.gis.ward}, Zone: {context.evidence_bundle.gis.zone}"),
            ReportSection(section_id="SEC-05-COMPLIANCE", title="Compliance Summary", content_summary=f"Score: {context.evidence_bundle.compliance.score}/100, Rules: {context.evidence_bundle.compliance.rules_checked}"),
            ReportSection(section_id="SEC-06-RULES", title="Rule Evaluation Table", content_summary=f"{len(context.evidence_bundle.compliance.rule_results)} detailed rule items"),
            ReportSection(section_id="SEC-07-RECS", title="Recommendations", content_summary=f"{context.recommendations.total_recommendations} actionable recommendations"),
            ReportSection(section_id="SEC-08-DECISION", title="Decision Summary", content_summary=f"Sanction Verdict: {context.approval.status_category}"),
            ReportSection(section_id="SEC-09-APPENDIX", title="Appendix", content_summary="GIS Provenance Citations & Software Versions"),
            ReportSection(section_id="SEC-10-AUDIT", title="Audit Metadata", content_summary=f"SHA256: {checksum_sha256[:16]}..."),
        ]

        return ReportData(
            report_id=report_id,
            generated_at=datetime.now(timezone.utc),
            decision_context=context,
            qr_code_base64=qr_b64,
            checksum_sha256=checksum_sha256,
            sections=sections,
        )
