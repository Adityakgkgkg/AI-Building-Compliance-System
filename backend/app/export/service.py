"""
MCRDSE Sprint 4 – Export Service Layer
======================================
Service orchestrator for generating municipal compliance reports (PDF, HTML, JSON)
and saving audit trail records.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple, Union

from app.decision.schemas import DecisionContext
from app.decision.service import DecisionService
from app.export.audit_service import AuditTrailService
from app.export.builder import ReportBuilder
from app.export.html_generator import HTMLReportGenerator
from app.export.json_exporter import JSONReportExporter
from app.export.pdf_generator import PDFReportGenerator
from app.export.schemas import ExportResponse, ReportData
from app.report.schemas import ModuleErrorDetail

logger = logging.getLogger("app.export.service")

ServiceResult = Union[ExportResponse, Tuple[ModuleErrorDetail, int]]


class ExportService:
    """
    Orchestration service for report generation and audit logging.
    """

    @staticmethod
    def generate_report(
        ifc_file: str,
        lat: float,
        lon: float,
        requested_formats: Optional[List[str]] = None,
        db: Optional[object] = None,
        host_base_url: str = "http://localhost:8000",
    ) -> ServiceResult:
        """
        Orchestrate report generation across PDF, HTML, and JSON formats.

        Returns
        -------
        ExportResponse or (ModuleErrorDetail, status_code)
        """
        if requested_formats is None:
            requested_formats = ["pdf", "html", "json"]

        # Fetch decision context
        context_result = DecisionService.get_decision_context(ifc_file=ifc_file, lat=lat, lon=lon)
        if isinstance(context_result, tuple):
            return context_result

        context: DecisionContext = context_result

        # Build canonical ReportData
        report_data = ReportBuilder.build_report_data(context=context, host_base_url=host_base_url)

        # Generate outputs
        pdf_bytes = PDFReportGenerator.generate_pdf(report_data)
        html_str = HTMLReportGenerator.generate_html(report_data)
        json_str = JSONReportExporter.export_json_str(report_data)

        # Save files and record audit trail
        audit_record = AuditTrailService.save_report(
            report_data=report_data,
            pdf_bytes=pdf_bytes,
            html_str=html_str,
            json_str=json_str,
            host_base_url=host_base_url,
            db=db,
        )

        return ExportResponse(
            report_id=report_data.report_id,
            status="COMPLETED",
            available_formats=requested_formats,
            created_at=report_data.generated_at,
            checksum_sha256=report_data.checksum_sha256,
            audit_record=audit_record,
        )
