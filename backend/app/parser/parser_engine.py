"""
MCRDSE Module 1 – IFC Parser Engine Core
========================================
Responsible ONLY for opening IFC files using IfcOpenShell, validating file
integrity, and checking schema compatibility (IFC2X3, IFC4, IFC4X3).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import ifcopenshell
from app.parser.exceptions import (
    InvalidIFCFileError,
    UnsupportedIFCSchemaError,
)

logger = logging.getLogger("app.parser.parser_engine")

_SUPPORTED_SCHEMAS = {"IFC2X3", "IFC4", "IFC4X3", "IFC4X3_ADD2", "IFC4X3_RC1"}


class IFCParserEngine:
    """
    Core IFC File Loader and Schema Validator.
    """

    @staticmethod
    def open_model(file_path: Path) -> Any:
        """
        Open an IFC file using IfcOpenShell and validate schema.

        Parameters
        ----------
        file_path:
            Path to the IFC file.

        Returns
        -------
        ifcopenshell.file
            Loaded IfcOpenShell file object.

        Raises
        ------
        InvalidIFCFileError
            If file is corrupt, empty, or not valid IFC syntax.
        UnsupportedIFCSchemaError
            If schema is not IFC2X3, IFC4, or IFC4X3.
        """
        if file_path.stat().st_size == 0:
            raise InvalidIFCFileError(detail=f"IFC file '{file_path.name}' is empty (0 bytes).")

        try:
            model = ifcopenshell.open(str(file_path))
        except Exception as exc:
            logger.error("Failed to open IFC file '%s' | error=%s", file_path.name, exc)
            raise InvalidIFCFileError(
                detail=f"Corrupt or invalid IFC file format in '{file_path.name}': {exc}"
            ) from exc

        # Extract schema
        try:
            schema_str = getattr(model, "schema", None)
            if not schema_str and hasattr(model, "wrapped_data"):
                header = model.wrapped_data.header
                if header and hasattr(header, "file_schema") and header.file_schema.schema_identifiers:
                    schema_str = header.file_schema.schema_identifiers[0]

            schema_str = (schema_str or "UNKNOWN").upper().strip()
        except Exception as exc:
            logger.warning("Could not read schema header from '%s' | error=%s", file_path.name, exc)
            schema_str = "UNKNOWN"

        # Validate schema compatibility
        matched = False
        for sup in _SUPPORTED_SCHEMAS:
            if sup in schema_str or schema_str in sup:
                matched = True
                break

        if not matched and schema_str != "UNKNOWN":
            # Check basic prefix
            if not (schema_str.startswith("IFC2X3") or schema_str.startswith("IFC4")):
                raise UnsupportedIFCSchemaError(
                    detail=(
                        f"Unsupported IFC schema '{schema_str}' in file '{file_path.name}'. "
                        f"Supported schemas: IFC2X3, IFC4, IFC4X3."
                    )
                )

        logger.info("Successfully opened IFC model '%s' | schema=%s", file_path.name, schema_str)
        return model
