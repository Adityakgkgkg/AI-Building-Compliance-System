"""
MCRDSE Sprint 3 – Decision Support REST API Router
===================================================
FastAPI router exposing the 5 decision support endpoints:
- GET /api/v1/decision/context
- GET /api/v1/decision/recommendations
- GET /api/v1/decision/approval
- GET /api/v1/decision/risk
- GET /api/v1/decision/summary
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.decision.schemas import (
    ApprovalReadiness,
    DecisionContext,
    DecisionSummary,
    RecommendationResponse,
    RiskAssessment,
)
from app.decision.service import DecisionService
from app.report.schemas import ModuleErrorDetail

router = APIRouter(prefix="/decision", tags=["Decision Support"])


@router.get(
    "/context",
    response_model=DecisionContext,
    responses={
        200: {"description": "Full decision context (evidence + decision analysis)."},
        503: {"model": ModuleErrorDetail, "description": "Upstream module unavailable."},
        500: {"model": ModuleErrorDetail, "description": "Evidence collection failure."},
    },
    summary="Fetch Full Decision Context",
)
def get_decision_context(
    ifc_file: str = Query(..., description="Filename of the uploaded IFC building plan."),
    lat: float = Query(..., ge=-90.0, le=90.0, description="WGS84 latitude of the building site."),
    lon: float = Query(..., ge=-180.0, le=180.0, description="WGS84 longitude of the building site."),
):
    """
    Return full aggregated decision context containing evidence bundle + decision support analysis.
    """
    result = DecisionService.get_decision_context(ifc_file=ifc_file, lat=lat, lon=lon)
    if isinstance(result, tuple):
        error_detail, status_code = result
        return JSONResponse(status_code=status_code, content=error_detail.model_dump(mode="json"))
    return result


@router.get(
    "/recommendations",
    response_model=RecommendationResponse,
    responses={
        200: {"description": "Prioritized evidence-based recommendations."},
        503: {"model": ModuleErrorDetail, "description": "Upstream module unavailable."},
    },
    summary="Fetch Actionable Recommendations",
)
def get_recommendations(
    ifc_file: str = Query(..., description="Filename of the uploaded IFC building plan."),
    lat: float = Query(..., ge=-90.0, le=90.0, description="WGS84 latitude of the building site."),
    lon: float = Query(..., ge=-180.0, le=180.0, description="WGS84 longitude of the building site."),
):
    """
    Return evidence-backed, prioritized recommendation items.
    """
    result = DecisionService.get_recommendations(ifc_file=ifc_file, lat=lat, lon=lon)
    if isinstance(result, tuple):
        error_detail, status_code = result
        return JSONResponse(status_code=status_code, content=error_detail.model_dump(mode="json"))
    return result


@router.get(
    "/approval",
    response_model=ApprovalReadiness,
    responses={
        200: {"description": "Approval readiness evaluation and sanction verdict."},
        503: {"model": ModuleErrorDetail, "description": "Upstream module unavailable."},
    },
    summary="Fetch Approval Readiness Score & Verdict",
)
def get_approval_readiness(
    ifc_file: str = Query(..., description="Filename of the uploaded IFC building plan."),
    lat: float = Query(..., ge=-90.0, le=90.0, description="WGS84 latitude of the building site."),
    lon: float = Query(..., ge=-180.0, le=180.0, description="WGS84 longitude of the building site."),
):
    """
    Return weighted approval readiness score, status category, and sanction verdict.
    """
    result = DecisionService.get_approval_readiness(ifc_file=ifc_file, lat=lat, lon=lon)
    if isinstance(result, tuple):
        error_detail, status_code = result
        return JSONResponse(status_code=status_code, content=error_detail.model_dump(mode="json"))
    return result


@router.get(
    "/risk",
    response_model=RiskAssessment,
    responses={
        200: {"description": "Multi-dimensional risk assessment."},
        503: {"model": ModuleErrorDetail, "description": "Upstream module unavailable."},
    },
    summary="Fetch Multi-Dimensional Risk Assessment",
)
def get_risk_assessment(
    ifc_file: str = Query(..., description="Filename of the uploaded IFC building plan."),
    lat: float = Query(..., ge=-90.0, le=90.0, description="WGS84 latitude of the building site."),
    lon: float = Query(..., ge=-180.0, le=180.0, description="WGS84 longitude of the building site."),
):
    """
    Return 4-dimensional risk evaluation (Environmental, Zoning, Structural, Compliance).
    """
    result = DecisionService.get_risk_assessment(ifc_file=ifc_file, lat=lat, lon=lon)
    if isinstance(result, tuple):
        error_detail, status_code = result
        return JSONResponse(status_code=status_code, content=error_detail.model_dump(mode="json"))
    return result


@router.get(
    "/summary",
    response_model=DecisionSummary,
    responses={
        200: {"description": "Executive decision summary for municipal officers."},
        503: {"model": ModuleErrorDetail, "description": "Upstream module unavailable."},
    },
    summary="Fetch Executive Decision Summary",
)
def get_decision_summary(
    ifc_file: str = Query(..., description="Filename of the uploaded IFC building plan."),
    lat: float = Query(..., ge=-90.0, le=90.0, description="WGS84 latitude of the building site."),
    lon: float = Query(..., ge=-180.0, le=180.0, description="WGS84 longitude of the building site."),
):
    """
    Return executive decision summary and action plan for sanctioning officers.
    """
    result = DecisionService.get_decision_summary(ifc_file=ifc_file, lat=lat, lon=lon)
    if isinstance(result, tuple):
        error_detail, status_code = result
        return JSONResponse(status_code=status_code, content=error_detail.model_dump(mode="json"))
    return result
