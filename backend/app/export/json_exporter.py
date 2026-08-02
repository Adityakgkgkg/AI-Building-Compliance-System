"""
MCRDSE Sprint 4 – JSON Report Exporter
======================================
Produces formatted, canonical JSON exports of the full report & evidence payload.
"""

from __future__ import annotations

import json
from app.export.schemas import ReportData


class JSONReportExporter:
    """
    JSON export generator for municipal report data.
    """

    @staticmethod
    def export_json_dict(report_data: ReportData) -> dict:
        """
        Return serialised dictionary representation of ReportData.
        """
        return report_data.model_dump(mode="json")

    @staticmethod
    def export_json_str(report_data: ReportData, indent: int = 2) -> str:
        """
        Return formatted JSON string of ReportData.
        """
        d = report_data.model_dump(mode="json")
        return json.dumps(d, indent=indent, ensure_ascii=False)
