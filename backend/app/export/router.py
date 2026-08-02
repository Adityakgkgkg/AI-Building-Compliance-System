"""
MCRDSE Sprint 4 – Report Export REST API Router
================================================
FastAPI router exposing the 5 report export & audit endpoints:
- POST /api/v1/export/generate
- GET  /api/v1/export/pdf/{report_id}
- GET  /api/v1/export/html/{report_id}
- GET  /api/v1/export/json/{report_id}
- GET  /api/v1/export/status/{report_id}
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse

from app.export.audit_service import AuditTrailService
from app.export.schemas import AuditRecordSchema, ExportRequest, ExportResponse
from app.export.service import ExportService
from app.report.schemas import ModuleErrorDetail

router = APIRouter(prefix="/export", tags=["Report Export Engine"])


@router.post(
    "/generate",
    response_model=ExportResponse,
    responses={
        200: {"description": "Report generated and audit record logged."},
        503: {"model": ModuleErrorDetail, "description": "Upstream module unavailable."},
    },
    summary="Generate Municipal Compliance Report (PDF/HTML/JSON)",
)
def generate_report(payload: ExportRequest, request: Request):
    """
    Generate a full municipal compliance report in PDF, HTML, and JSON formats.
    """
    base_url = str(request.base_url).rstrip("/")
    result = ExportService.generate_report(
        ifc_file=payload.ifc_file,
        lat=payload.lat,
        lon=payload.lon,
        requested_formats=payload.formats,
        host_base_url=base_url,
    )
    if isinstance(result, tuple):
        error_detail, status_code = result
        return JSONResponse(status_code=status_code, content=error_detail.model_dump(mode="json"))
    return result


@router.get(
    "/pdf/{report_id}",
    response_class=Response,
    responses={
        200: {"content": {"application/pdf": {}}, "description": "Binary PDF report file."},
        404: {"description": "Report ID not found."},
    },
    summary="Download PDF Report",
)
def get_pdf_report(report_id: str):
    """
    Retrieve binary PDF file for a generated report.
    """
    pdf_bytes = AuditTrailService.get_pdf_bytes(report_id)
    if not pdf_bytes:
        raise HTTPException(status_code=404, detail=f"PDF report '{report_id}' not found.")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=compliance_report_{report_id}.pdf"},
    )


@router.get(
    "/html/{report_id}",
    response_class=HTMLResponse,
    responses={
        200: {"description": "Responsive HTML report content."},
        404: {"description": "Report ID not found."},
    },
    summary="View Responsive HTML Report",
)
def get_html_report(report_id: str):
    """
    Retrieve HTML string for a generated report.
    """
    html_str = AuditTrailService.get_html_str(report_id)
    if not html_str:
        raise HTTPException(status_code=404, detail=f"HTML report '{report_id}' not found.")

    return HTMLResponse(content=html_str)


@router.get(
    "/json/{report_id}",
    response_class=JSONResponse,
    responses={
        200: {"description": "Structured JSON report payload."},
        404: {"description": "Report ID not found."},
    },
    summary="Fetch Canonical JSON Report Payload",
)
def get_json_report(report_id: str):
    """
    Retrieve canonical JSON data payload for a generated report.
    """
    json_dict = AuditTrailService.get_json_dict(report_id)
    if not json_dict:
        raise HTTPException(status_code=404, detail=f"JSON report '{report_id}' not found.")

    return JSONResponse(content=json_dict)


@router.get(
    "/status/{report_id}",
    response_model=AuditRecordSchema,
    responses={
        200: {"description": "Audit record and verification status."},
        404: {"description": "Report ID not found."},
    },
    summary="Verify Report Authenticity & Audit Status",
)
def get_report_status(report_id: str):
    """
    Retrieve audit record and verification details for a report ID.
    """
    audit = AuditTrailService.get_audit_record(report_id)
    if not audit:
        raise HTTPException(status_code=404, detail=f"Audit record for report '{report_id}' not found.")

    return audit
