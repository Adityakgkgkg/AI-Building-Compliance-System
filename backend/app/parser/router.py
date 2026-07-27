"""
AI Building Compliance System — IFC Parser Router

Exposes four REST endpoints under /api/v1/parser/.
All business logic is delegated to ParserService — these route
handlers are intentionally thin: validate input, call service, return response.

Endpoints:
    POST   /api/v1/parser/upload           — upload & validate an IFC file
    POST   /api/v1/parser/parse/{file_id}  — parse a previously uploaded file
    GET    /api/v1/parser/building/{file_id} — retrieve building metadata
    GET    /api/v1/parser/elements/{file_id} — retrieve element counts
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from app.parser.schemas import (
    BuildingInfo,
    ElementCounts,
    ErrorResponse,
    ParseResult,
    UploadIFCResponse,
)
from app.parser.service import ParserService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/parser", tags=["IFC Parser"])

# Single service instance (stateless orchestrator; store is the singleton)
_service = ParserService()


# ── POST /upload ─────────────────────────────────────────────────

@router.post(
    "/upload",
    response_model=UploadIFCResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload IFC File",
    description=(
        "Upload a `.ifc` building model file. "
        "Returns a `file_id` UUID used in subsequent parse and query calls. "
        "Validates extension, file size, and IFC STEP header before saving."
    ),
    responses={
        400: {"model": ErrorResponse, "description": "Missing filename or empty file."},
        413: {"model": ErrorResponse, "description": "File exceeds maximum allowed size."},
        422: {"model": ErrorResponse, "description": "Invalid extension or corrupt IFC header."},
    },
)
async def upload_ifc(
    file: UploadFile = File(..., description="IFC building model file (.ifc only)"),
) -> UploadIFCResponse:
    """
    Validate and save an IFC file, returning a ``file_id`` for subsequent calls.

    The file_id is a UUID4 string that uniquely identifies this upload
    across all parser endpoints.
    """
    logger.info("POST /parser/upload — filename='%s'", file.filename)
    return await _service.upload_ifc(file)


# ── POST /parse/{file_id} ────────────────────────────────────────

@router.post(
    "/parse/{file_id}",
    response_model=ParseResult,
    status_code=status.HTTP_200_OK,
    summary="Parse IFC File",
    description=(
        "Open and parse a previously uploaded IFC file using IfcOpenShell. "
        "Extracts building metadata, element counts, and best-effort geometry. "
        "Result is cached and accessible via the GET endpoints."
    ),
    responses={
        404: {"model": ErrorResponse, "description": "file_id not found or file missing on disk."},
        422: {"model": ErrorResponse, "description": "Corrupt IFC, unsupported schema, or missing IfcProject."},
        500: {"model": ErrorResponse, "description": "Unexpected extraction error."},
    },
)
def parse_ifc(file_id: str) -> ParseResult:
    """
    Parse the IFC file identified by ``file_id``.

    This call can be repeated — subsequent calls re-parse and overwrite
    the cached result. Returns the complete ParseResult JSON contract.
    """
    logger.info("POST /parser/parse/%s", file_id)
    return _service.parse_ifc(file_id)


# ── GET /building/{file_id} ──────────────────────────────────────

@router.get(
    "/building/{file_id}",
    response_model=BuildingInfo,
    status_code=status.HTTP_200_OK,
    summary="Get Building Metadata",
    description=(
        "Retrieve only the building metadata section of a previously parsed IFC file. "
        "The file must have been parsed via POST /parse/{file_id} first."
    ),
    responses={
        404: {"model": ErrorResponse, "description": "file_id not found or not yet parsed."},
    },
)
def get_building(file_id: str) -> BuildingInfo:
    """
    Return the ``building`` section of the ParseResult for *file_id*.

    Intended for consumers (compliance engine, UI) that only need
    project-level metadata without element or geometry data.
    """
    logger.info("GET /parser/building/%s", file_id)
    return _service.get_building(file_id)


# ── GET /elements/{file_id} ──────────────────────────────────────

@router.get(
    "/elements/{file_id}",
    response_model=ElementCounts,
    status_code=status.HTTP_200_OK,
    summary="Get Element Counts",
    description=(
        "Retrieve only the element counts section of a previously parsed IFC file. "
        "The file must have been parsed via POST /parse/{file_id} first."
    ),
    responses={
        404: {"model": ErrorResponse, "description": "file_id not found or not yet parsed."},
    },
)
def get_elements(file_id: str) -> ElementCounts:
    """
    Return the ``elements`` section of the ParseResult for *file_id*.

    Intended for the compliance engine (Sprint 3) which reads element
    counts to check against building codes.
    """
    logger.info("GET /parser/elements/%s", file_id)
    return _service.get_elements(file_id)
