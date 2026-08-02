"""
MCRDSE Analysis Orchestrator – REST API Router
===============================================
FastAPI router exposing:
- POST /api/v1/analyze
- GET  /api/v1/analyze/progress/{analysis_id}
- GET  /api/v1/analyze/{analysis_id}
"""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import JSONResponse

from app.orchestrator.schemas import AnalysisProgressResponse, UnifiedAnalysisResponse
from app.orchestrator.service import OrchestratorService
from app.report.schemas import ModuleErrorDetail

router = APIRouter(prefix="/analyze", tags=["Analysis Orchestrator"])


@router.post(
    "",
    response_model=UnifiedAnalysisResponse,
    responses={
        200: {"description": "End-to-end analysis completed successfully."},
        400: {"model": ModuleErrorDetail, "description": "Invalid file upload or parameter error."},
        503: {"model": ModuleErrorDetail, "description": "Upstream module execution failure."},
    },
    summary="Automated End-to-End Building Compliance Analysis",
    description="Upload an IFC file to automatically parse, classify, run GIS spatial analysis, evaluate compliance rules, assemble evidence, generate decision support, and export PDF/HTML/JSON reports in a single call.",
)
async def analyze_building_plan(
    request: Request,
    file: UploadFile = File(..., description="IFC building plan file"),
    lat: float = Query(12.9250, ge=-90.0, le=90.0, description="WGS84 latitude of site"),
    lon: float = Query(77.5938, ge=-180.0, le=180.0, description="WGS84 longitude of site"),
):
    if not file.filename or not file.filename.lower().endswith(".ifc"):
        raise HTTPException(status_code=400, detail="Only .ifc files are supported for automated compliance analysis.")

    file_bytes = await file.read()
    base_url = str(request.base_url).rstrip("/")

    result = OrchestratorService.analyze_ifc(
        ifc_file_bytes=file_bytes,
        filename=file.filename,
        lat=lat,
        lon=lon,
        host_base_url=base_url,
    )

    if isinstance(result, tuple):
        error_detail, status_code = result
        return JSONResponse(status_code=status_code, content=error_detail.model_dump(mode="json"))

    return result


@router.get(
    "/progress/{analysis_id}",
    response_model=AnalysisProgressResponse,
    summary="Fetch Analysis Progress Status",
)
def get_analysis_progress(analysis_id: str):
    prog = OrchestratorService.get_progress(analysis_id)
    if not prog:
        raise HTTPException(status_code=404, detail=f"Analysis run '{analysis_id}' not found.")
    return prog


@router.get(
    "/{analysis_id}",
    response_model=UnifiedAnalysisResponse,
    summary="Fetch Unified Analysis Results",
)
def get_analysis_results(analysis_id: str):
    res = OrchestratorService.get_result(analysis_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"Analysis results for '{analysis_id}' not found.")
    return res
