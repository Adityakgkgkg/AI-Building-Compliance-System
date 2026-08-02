"""
MCRDSE Sprint 1 – Evidence Collection Router
=============================================
FastAPI router exposing the single Sprint 1 endpoint:

    GET /api/v1/report/context

This endpoint accepts an IFC filename and a WGS84 coordinate pair, invokes
``ReportService.collect_evidence()``, and returns either:

- **HTTP 200** — A fully assembled ``EvidenceBundle`` in JSON form.
- **HTTP 503** — A ``ModuleErrorDetail`` envelope when an upstream module
  (IFC Parser, Classification, GIS, or Compliance Engine) is unavailable.
- **HTTP 422** — Standard FastAPI validation error when query parameters
  are missing or out of range.
- **HTTP 500** — Internal server error for unexpected failures.

Design rules:
- No business logic lives here.
- The router delegates entirely to ``ReportService``.
- Response models are explicit so OpenAPI documentation is accurate.
"""

from __future__ import annotations

import logging
from typing import Union

from fastapi import APIRouter, Query, Response, status
from fastapi.responses import JSONResponse

from app.report.schemas import EvidenceBundle, ModuleErrorDetail
from app.report.service import ReportService

logger = logging.getLogger("app.report.router")

router = APIRouter(
    prefix="/report",
    tags=["Municipal Compliance Reporting & Decision Support Engine (MCRDSE)"],
)


@router.get(
    "/context",
    summary="Collect Unified Evidence Bundle",
    description=(
        "Aggregates outputs from the IFC Parser (Module 1), Building Classification "
        "(Module 2), GIS Context Engine (Module 3), and Compliance Engine into a "
        "single canonical ``EvidenceBundle`` object. "
        "This endpoint is the single source of truth for all downstream reporting. "
        "Returns HTTP 503 with a structured error envelope when any upstream module "
        "is unavailable, rather than an opaque 500."
    ),
    response_model=EvidenceBundle,
    responses={
        200: {
            "description": "Fully assembled EvidenceBundle from all upstream modules.",
            "model": EvidenceBundle,
        },
        503: {
            "description": "One or more upstream modules are unavailable.",
            "model": ModuleErrorDetail,
        },
        500: {
            "description": "Unexpected internal error during bundle assembly.",
        },
    },
)
async def get_evidence_bundle(
    ifc_file: str = Query(
        ...,
        description="Filename of the uploaded IFC building plan file to analyse.",
        examples=["building_plan.ifc"],
    ),
    lat: float = Query(
        ...,
        ge=-90.0,
        le=90.0,
        description="WGS84 latitude of the building site.",
        examples=[12.9250],
    ),
    lon: float = Query(
        ...,
        ge=-180.0,
        le=180.0,
        description="WGS84 longitude of the building site.",
        examples=[77.5938],
    ),
) -> Union[EvidenceBundle, Response]:
    """
    Collect and return the canonical ``EvidenceBundle`` for a building plan.

    Query Parameters
    ----------------
    ifc_file : str
        Filename of the uploaded IFC file.
    lat : float
        WGS84 latitude (−90 … 90).
    lon : float
        WGS84 longitude (−180 … 180).
    """
    logger.info(
        "GET /report/context | ifc_file=%s lat=%.6f lon=%.6f",
        ifc_file,
        lat,
        lon,
    )

    result = ReportService.collect_evidence(
        ifc_file=ifc_file,
        lat=lat,
        lon=lon,
        persist=False,
    )

    # Success path — return the canonical bundle
    if isinstance(result, EvidenceBundle):
        return result

    # Failure path — return structured error with correct HTTP status
    error_detail, http_status = result
    logger.warning(
        "Returning structured module error | code=%s module=%s status=%d",
        error_detail.error_code,
        error_detail.module,
        http_status,
    )
    return JSONResponse(
        status_code=http_status,
        content=error_detail.model_dump(mode="json"),
    )
