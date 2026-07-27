"""
AI Building Compliance System — IFC Parser Service

Orchestrates the full IFC pipeline:
    upload → validate → save → open → extract → serialize

This is the only module that coordinates the sub-components.
Routers depend on ParserService; sub-components do not depend on each other.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile, status

from app.parser.element_extractor import ElementExtractor
from app.parser.file_loader import IFCFileLoader
from app.parser.metadata_extractor import MetadataExtractor
from app.parser.models import FileStatus, IFCFileRecord, ParsedFileStore, file_store
from app.parser.schemas import (
    BuildingInfo,
    ElementCounts,
    ParseResult,
    UploadIFCResponse,
)
from app.parser.serializer import ParseResultSerializer
from app.parser.utils import extract_geometry

logger = logging.getLogger(__name__)


class ParserService:
    """
    Orchestrates IFC file upload and parsing pipeline.

    Dependencies are injected to facilitate unit testing:
        - store: ParsedFileStore (defaults to module-level singleton)
        - loader: IFCFileLoader
        - metadata_extractor: MetadataExtractor
        - element_extractor: ElementExtractor
        - serializer: ParseResultSerializer

    All business logic lives here. The router only calls these methods.
    """

    def __init__(
        self,
        store: ParsedFileStore | None = None,
        loader: IFCFileLoader | None = None,
        metadata_extractor: MetadataExtractor | None = None,
        element_extractor: ElementExtractor | None = None,
        serializer: ParseResultSerializer | None = None,
    ) -> None:
        self._store = store or file_store
        self._loader = loader or IFCFileLoader()
        self._metadata = metadata_extractor or MetadataExtractor()
        self._elements = element_extractor or ElementExtractor()
        self._serializer = serializer or ParseResultSerializer()

    # ── Step 1: Upload ────────────────────────────────────────────

    async def upload_ifc(self, upload_file: UploadFile) -> UploadIFCResponse:
        """
        Validate and save an uploaded IFC file.

        Args:
            upload_file: FastAPI UploadFile from the multipart request.

        Returns:
            UploadIFCResponse with file_id, filename, and status='uploaded'.

        Raises:
            HTTPException: propagated from IFCFileLoader on validation failure.
        """
        logger.info("Upload started: filename='%s'", upload_file.filename)

        record: IFCFileRecord = await self._loader.validate_and_save(upload_file)
        self._store.save(record)

        logger.info(
            "Upload complete: file_id=%s filename=%s",
            record.file_id,
            record.filename,
        )
        return UploadIFCResponse(
            file_id=record.file_id,
            filename=record.filename,
            status="uploaded",
        )

    # ── Step 2: Parse ─────────────────────────────────────────────

    def parse_ifc(self, file_id: str) -> ParseResult:
        """
        Open, parse, and extract data from a previously uploaded IFC file.

        Steps:
            1. Retrieve the file record (raises 404 if unknown).
            2. Open IFC with IfcOpenShell.
            3. Validate the model has at least one IfcProject.
            4. Extract metadata, element counts, and geometry.
            5. Serialize and cache the result.

        Args:
            file_id: UUID string returned by upload_ifc().

        Returns:
            ParseResult — the canonical JSON contract.

        Raises:
            HTTPException 404: file_id not found.
            HTTPException 422: corrupt IFC or unsupported schema.
            HTTPException 500: unexpected internal error.
        """
        record = self._get_record_or_404(file_id)
        logger.info(
            "Parse started: file_id=%s filename=%s", file_id, record.filename
        )
        self._store.update_status(file_id, FileStatus.PARSING)

        ifc_model = self._open_ifc(record.file_path, file_id)
        self._validate_model(ifc_model, file_id)

        try:
            building: BuildingInfo = self._metadata.extract(ifc_model)
            elements: ElementCounts = self._elements.extract(ifc_model)
            geometry_dict: dict = extract_geometry(ifc_model)

            result: ParseResult = self._serializer.serialize(
                building, elements, geometry_dict
            )
        except Exception as exc:
            self._store.update_status(file_id, FileStatus.ERROR, str(exc))
            logger.exception("Extraction failed for file_id=%s: %s", file_id, exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while extracting building data.",
            ) from exc

        self._store.save_result(file_id, result)
        self._store.update_status(file_id, FileStatus.PARSED)
        logger.info("Parse complete: file_id=%s", file_id)
        return result

    # ── Step 3 & 4: Getters ───────────────────────────────────────

    def get_building(self, file_id: str) -> BuildingInfo:
        """
        Return only the BuildingInfo section of a parsed result.

        Args:
            file_id: UUID string returned by upload_ifc().

        Returns:
            BuildingInfo for the given file.

        Raises:
            HTTPException 404: file_id not found or not yet parsed.
        """
        result = self._get_result_or_404(file_id)
        return result.building

    def get_elements(self, file_id: str) -> ElementCounts:
        """
        Return only the ElementCounts section of a parsed result.

        Args:
            file_id: UUID string returned by upload_ifc().

        Returns:
            ElementCounts for the given file.

        Raises:
            HTTPException 404: file_id not found or not yet parsed.
        """
        result = self._get_result_or_404(file_id)
        return result.elements

    # ── Private helpers ───────────────────────────────────────────

    def _get_record_or_404(self, file_id: str) -> IFCFileRecord:
        """Retrieve the file record or raise 404."""
        record = self._store.get(file_id)
        if record is None:
            logger.warning("file_id not found in store: %s", file_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No file found for file_id '{file_id}'. "
                       "Please upload the file first via POST /api/v1/parser/upload.",
            )
        return record

    def _get_result_or_404(self, file_id: str) -> ParseResult:
        """Retrieve a cached ParseResult or raise 404."""
        self._get_record_or_404(file_id)  # validates file_id exists
        result = self._store.get_result(file_id)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"No parse result found for file_id '{file_id}'. "
                    "Please parse the file first via POST /api/v1/parser/parse/{file_id}."
                ),
            )
        return result

    @staticmethod
    def _open_ifc(file_path: Path, file_id: str) -> Any:
        """
        Open an IFC file using IfcOpenShell.

        Raises:
            HTTPException 422: if IfcOpenShell cannot open the file.
        """
        try:
            import ifcopenshell  # noqa: PLC0415

            if not file_path.exists():
                raise FileNotFoundError(f"File not on disk: {file_path}")

            model = ifcopenshell.open(str(file_path))
            logger.debug("IfcOpenShell opened: %s", file_path.name)
            return model

        except FileNotFoundError as exc:
            logger.error("File not found on disk for file_id=%s: %s", file_id, exc)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The IFC file could not be found on the server. "
                       "Please re-upload the file.",
            ) from exc

        except Exception as exc:
            logger.error(
                "IfcOpenShell failed to open file_id=%s: %s", file_id, exc
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    "The IFC file could not be parsed. It may be corrupt, "
                    f"truncated, or use an unsupported schema. Detail: {exc}"
                ),
            ) from exc

    @staticmethod
    def _validate_model(ifc_model: Any, file_id: str) -> None:
        """
        Validate that the model contains at least one IfcProject.

        A valid IFC file must have exactly one IfcProject at its root.
        Missing IfcProject usually indicates a non-building IFC file
        or a severely malformed export.

        Raises:
            HTTPException 422: IfcProject entity is absent.
        """
        try:
            projects = ifc_model.by_type("IfcProject")
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not query IFC entities. The file may be corrupt.",
            ) from exc

        if not projects:
            logger.warning(
                "IFC model has no IfcProject: file_id=%s", file_id
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "The IFC file does not contain an IfcProject entity. "
                    "This is required for a valid building IFC file."
                ),
            )
