"""
AI Building Compliance System — IFC File Loader

Handles validation, saving, and file_id generation for uploaded IFC files.
All validation errors raise HTTPException with appropriate status codes
so the router can return clean API responses.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import get_settings
from app.parser.models import IFCFileRecord

logger = logging.getLogger(__name__)
settings = get_settings()

# IFC files must be uploaded to a dedicated subdirectory
_IFC_SUBDIR = "ifc"


class IFCFileLoader:
    """
    Validates and persists an uploaded IFC file.

    Validation chain (in order):
        1. Filename present
        2. Extension is .ifc (only)
        3. File content is not empty
        4. File size ≤ MAX_UPLOAD_SIZE_MB
        5. IFC header sanity check (starts with 'ISO-10303')

    On success: saves the file to ``uploads/ifc/<file_id>_<filename>``
    and returns an IFCFileRecord.
    """

    ALLOWED_EXTENSION = ".ifc"

    def __init__(self) -> None:
        self._upload_root: Path = settings.upload_path / _IFC_SUBDIR
        self._upload_root.mkdir(parents=True, exist_ok=True)
        self._max_bytes: int = settings.max_upload_size_bytes

    # ── Public interface ──────────────────────────────────────────

    async def validate_and_save(self, upload_file: UploadFile) -> IFCFileRecord:
        """
        Validate *upload_file* and save it to disk.

        Args:
            upload_file: FastAPI UploadFile from the request.

        Returns:
            IFCFileRecord with a freshly generated file_id.

        Raises:
            HTTPException 400: Missing filename or empty file.
            HTTPException 413: File exceeds maximum allowed size.
            HTTPException 422: Wrong extension or corrupt IFC header.
        """
        filename = self._validate_filename(upload_file.filename)
        contents = await self._read_and_validate_contents(upload_file)
        self._validate_ifc_header(contents, filename)

        file_id = self._generate_file_id()
        file_path = self._save(file_id, filename, contents)

        record = IFCFileRecord(
            file_id=file_id,
            filename=filename,
            file_path=file_path,
        )
        logger.info(
            "IFC file saved: file_id=%s filename=%s size=%d bytes",
            file_id,
            filename,
            len(contents),
        )
        return record

    # ── Private helpers ───────────────────────────────────────────

    def _validate_filename(self, filename: str | None) -> str:
        """Ensure filename is present and has the .ifc extension."""
        if not filename:
            logger.warning("Upload rejected: no filename provided.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No filename provided. Please attach a file.",
            )

        ext = ("." + filename.rsplit(".", 1)[-1]).lower() if "." in filename else ""
        if ext != self.ALLOWED_EXTENSION:
            logger.warning(
                "Upload rejected: unsupported extension '%s' for file '%s'.",
                ext,
                filename,
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    f"Unsupported file type '{ext}'. "
                    "Only .ifc files are accepted by the parser endpoint."
                ),
            )
        return filename

    async def _read_and_validate_contents(self, upload_file: UploadFile) -> bytes:
        """Read the file bytes and enforce size constraints."""
        contents = await upload_file.read()

        if len(contents) == 0:
            logger.warning("Upload rejected: empty file.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded file is empty.",
            )

        if len(contents) > self._max_bytes:
            logger.warning(
                "Upload rejected: file size %d bytes exceeds limit %d bytes.",
                len(contents),
                self._max_bytes,
            )
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=(
                    f"File size ({len(contents):,} bytes) exceeds the maximum "
                    f"allowed size ({settings.MAX_UPLOAD_SIZE_MB} MB)."
                ),
            )
        return contents

    @staticmethod
    def _validate_ifc_header(contents: bytes, filename: str) -> None:
        """
        Perform a lightweight header check.

        Valid IFC files begin with 'ISO-10303-21' (STEP Physical File).
        This catches clearly corrupt or mis-labelled uploads before
        IfcOpenShell tries to open them.
        """
        header = contents[:20].strip().upper()
        if not header.startswith(b"ISO-10303-21"):
            logger.warning(
                "Upload rejected: file '%s' does not appear to be a valid IFC (STEP) file.",
                filename,
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    "The uploaded file does not appear to be a valid IFC file. "
                    "IFC files must begin with 'ISO-10303-21'."
                ),
            )

    @staticmethod
    def _generate_file_id() -> str:
        """Generate a UUID4 string as the file identifier."""
        return str(uuid.uuid4())

    def _save(self, file_id: str, filename: str, contents: bytes) -> Path:
        """Write *contents* to disk. Returns the saved file path."""
        safe_name = f"{file_id}_{filename}"
        file_path = self._upload_root / safe_name
        file_path.write_bytes(contents)
        return file_path
