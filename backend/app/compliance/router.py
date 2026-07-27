"""
AI Building Compliance System — Compliance Router v2

REST endpoints for Module 2: Municipal Rule Engine.

Endpoints:
    POST   /api/v1/compliance/check
           Run full 5-stage compliance check (inline parse_result).

    POST   /api/v1/compliance/check/{file_id}
           Run full 5-stage compliance check (by stored file_id).

    POST   /api/v1/compliance/classify
           Run Stage 1 Building Classification standalone.

    GET    /api/v1/compliance/report/{file_id}
           Retrieve cached compliance report.

    GET    /api/v1/compliance/building-types
           List supported building types and their descriptions.

    GET    /api/v1/compliance/rules
           List rules in a rule file.

    GET    /api/v1/compliance/rules/{rule_id}
           Get single rule detail.
"""

from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, Query, status

from app.compliance.schemas import (
    BuildingTypeInfo,
    ClassificationResult,
    ClassifyRequest,
    ComplianceErrorResponse,
    ComplianceReport,
    ComplianceRequest,
    RuleDetail,
)
from app.compliance.service import ComplianceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/compliance", tags=["Municipal Rule Engine"])

_service = ComplianceService()


# ── POST /check ───────────────────────────────────────────────────

@router.post(
    "/check",
    response_model=ComplianceReport,
    status_code=status.HTTP_200_OK,
    summary="Run Compliance Check (5-Stage Pipeline)",
    description=(
        "Executes the 5-stage Municipal Rule Engine pipeline: "
        "Classification -> Rule Selection -> Generic Evaluation -> Violation Analysis -> Report Generation. "
        "Accepts inline parse_result and site-specific building_params."
    ),
    responses={
        400: {"model": ComplianceErrorResponse, "description": "Missing required input."},
        422: {"model": ComplianceErrorResponse, "description": "Invalid rules file or bad input."},
    },
)
def check_compliance(request: ComplianceRequest) -> ComplianceReport:
    """Run full compliance check for inline parse_result or file_id."""
    logger.info("POST /compliance/check — file_id=%s", request.file_id)
    return _service.run_check(request)


# ── POST /check/{file_id} ─────────────────────────────────────────

@router.post(
    "/check/{file_id}",
    response_model=ComplianceReport,
    status_code=status.HTTP_200_OK,
    summary="Run Compliance Check (by file_id)",
    description="Run compliance check for a previously parsed IFC file.",
    responses={
        404: {"model": ComplianceErrorResponse, "description": "file_id not found."},
        422: {"model": ComplianceErrorResponse, "description": "Invalid rules file."},
    },
)
def check_compliance_by_file(
    file_id: str,
    request: ComplianceRequest,
) -> ComplianceReport:
    """Run compliance check using file_id from URL path."""
    logger.info("POST /compliance/check/%s", file_id)
    req_copy = request.model_copy(update={"file_id": file_id, "parse_result": None})
    return _service.run_check(req_copy)


# ── POST /classify ────────────────────────────────────────────────

@router.post(
    "/classify",
    response_model=ClassificationResult,
    status_code=status.HTTP_200_OK,
    summary="Classify Building (Stage 1 Standalone)",
    description=(
        "Run Stage 1 Building Classification Engine standalone. "
        "Determines building type (Residential House, Apartment, Commercial, etc.) "
        "using IFC metadata, spatial geometry, and feature heuristics."
    ),
)
def classify_building(request: ClassifyRequest) -> ClassificationResult:
    """Classify building type without running rule checks."""
    logger.info("POST /compliance/classify")
    return _service.classify_building(
        parse_data=request.parse_result,
        building_params=request.building_params,
    )


# ── GET /report/{file_id} ─────────────────────────────────────────

@router.get(
    "/report/{file_id}",
    response_model=ComplianceReport,
    status_code=status.HTTP_200_OK,
    summary="Get Cached Compliance Report",
    responses={
        404: {"model": ComplianceErrorResponse, "description": "Report not found."},
    },
)
def get_report(file_id: str) -> ComplianceReport:
    """Retrieve cached compliance report."""
    logger.info("GET /compliance/report/%s", file_id)
    return _service.get_cached_report(file_id)


# ── GET /building-types ───────────────────────────────────────────

@router.get(
    "/building-types",
    response_model=List[BuildingTypeInfo],
    status_code=status.HTTP_200_OK,
    summary="List Supported Building Types",
    description="Returns all recognised building types and their description.",
)
def list_building_types() -> List[BuildingTypeInfo]:
    """List supported BBMP building types."""
    return _service.list_building_types()


# ── GET /rules ────────────────────────────────────────────────────

@router.get(
    "/rules",
    response_model=List[RuleDetail],
    status_code=status.HTTP_200_OK,
    summary="List All Rules",
)
def list_rules(
    rules_file: str = Query(
        default="residential_house",
        description="Rule file stem (e.g., residential_house, apartment, commercial).",
    ),
) -> List[RuleDetail]:
    """List rules in the specified rule set."""
    logger.info("GET /compliance/rules?rules_file=%s", rules_file)
    return _service.list_rules(rules_file)


# ── GET /rules/{rule_id} ──────────────────────────────────────────

@router.get(
    "/rules/{rule_id}",
    response_model=RuleDetail,
    status_code=status.HTTP_200_OK,
    summary="Get Single Rule",
)
def get_rule(
    rule_id: str,
    rules_file: str = Query(
        default="residential_house",
        description="Rule file stem.",
    ),
) -> RuleDetail:
    """Get details of a single rule."""
    logger.info("GET /compliance/rules/%s?rules_file=%s", rule_id, rules_file)
    return _service.get_rule(rules_file, rule_id)
