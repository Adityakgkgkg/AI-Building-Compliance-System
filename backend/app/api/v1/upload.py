"""
AI Building Compliance System — File Upload Endpoint

Accepts IFC and DXF files, saves them to the configured uploads directory,
and returns metadata. No parsing is performed in Sprint 1.
"""

import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException, status

from app.core.config import get_settings
from app.schemas import UploadResponse
from app.utils import get_upload_time, get_file_extension

router = APIRouter(tags=["Upload"])
settings = get_settings()


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Building Plan",
    description="Upload an IFC or DXF building plan file for future processing.",
)
async def upload_file(
    file: UploadFile = File(..., description="IFC or DXF building plan file"),
) -> UploadResponse:
    """
    Receive a building plan file and store it in the uploads directory.

    Validation:
        - File must have an allowed extension (.ifc, .dxf)
        - File size must not exceed the configured maximum

    Returns:
        UploadResponse with filename, size, type, and upload timestamp.
    """

    # ── Validate filename ────────────────────────────────────────
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided.",
        )

    # ── Validate extension ───────────────────────────────────────
    extension = get_file_extension(file.filename)
    if extension not in settings.allowed_extensions_list:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"File type '{extension}' is not supported. "
                f"Allowed types: {', '.join(settings.allowed_extensions_list)}"
            ),
        )

    # ── Read file content ────────────────────────────────────────
    contents = await file.read()
    file_size = len(contents)

    # ── Validate file size ───────────────────────────────────────
    if file_size > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"File size ({file_size} bytes) exceeds the maximum "
                f"allowed size ({settings.MAX_UPLOAD_SIZE_MB} MB)."
            ),
        )

    # ── Save to disk ─────────────────────────────────────────────
    upload_path = settings.upload_path / file.filename
    with open(upload_path, "wb") as buffer:
        buffer.write(contents)

    # ── Return metadata ──────────────────────────────────────────
    return UploadResponse(
        filename=file.filename,
        size=file_size,
        type=extension,
        upload_time=get_upload_time(),
    )
