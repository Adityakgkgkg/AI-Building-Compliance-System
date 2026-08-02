"""
MCRDSE Module 1 – IFC Parser REST API Router
=============================================
FastAPI router exposing the IFC Parser endpoints:
- POST /api/v1/parser/upload
- GET  /api/v1/parser/health
- GET  /api/v1/parser/metadata
- GET  /api/v1/parser/statistics
"""

from __future__ import annotations

import ifcopenshell
from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.parser.exceptions import IFCParserError
from app.parser.schemas import (
    IFCHealthStatus,
    IFCMetadata,
    IFCParseSummary,
    IFCStatistics,
)
from app.parser.service import IFCParserService
from app.parser.utils import get_uploads_dir

router = APIRouter(prefix="/parser", tags=["IFC Parser Engine"])


@router.get(
    "/health",
    response_model=IFCHealthStatus,
    summary="Check IFC Parser Engine Health",
)
def get_parser_health():
    """
    Return health status and IfcOpenShell version.
    """
    ver = getattr(ifcopenshell, "__version__", "0.8.5")
    return IFCHealthStatus(
        status="healthy",
        ifcopenshell_version=str(ver),
        supported_schemas=["IFC2X3", "IFC4", "IFC4X3"],
    )


@router.post(
    "/upload",
    response_model=IFCParseSummary,
    summary="Upload and Parse IFC File",
)
async def upload_and_parse_ifc(file: UploadFile = File(...)):
    """
    Upload an IFC file, validate schema, extract building entities, and return summary.
    """
    if not file.filename or not file.filename.lower().endswith(".ifc"):
        raise HTTPException(status_code=400, detail="Only .ifc files are supported.")

    upload_path = get_uploads_dir() / file.filename
    try:
        content = await file.read()
        upload_path.write_bytes(content)
        summary = IFCParserService.parse_full(upload_path)
        return summary
    except IFCParserError as exc:
        raise HTTPException(status_code=400, detail=exc.as_dict())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected parsing error: {exc}")


@router.get(
    "/metadata",
    response_model=IFCMetadata,
    summary="Extract Metadata from IFC File",
)
def get_ifc_metadata(
    ifc_file: str = Query(..., description="IFC filename or path"),
):
    """
    Extract IFCMetadata for a specified file.
    """
    try:
        return IFCParserService.extract_metadata(ifc_file)
    except IFCParserError as exc:
        raise HTTPException(status_code=400, detail=exc.as_dict())


@router.get(
    "/statistics",
    response_model=IFCStatistics,
    summary="Extract Statistics from IFC File",
)
def get_ifc_statistics(
    ifc_file: str = Query(..., description="IFC filename or path"),
):
    """
    Extract IFCStatistics for a specified file.
    """
    try:
        return IFCParserService.extract_statistics(ifc_file)
    except IFCParserError as exc:
        raise HTTPException(status_code=400, detail=exc.as_dict())
