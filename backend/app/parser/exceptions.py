"""
MCRDSE Module 1 – IFC Parser Engine Exceptions
==============================================
Domain exception hierarchy for the IFC Parser module. All domain exceptions carry
a machine-readable ``code`` and a human-readable ``message`` or ``detail``.
"""

from __future__ import annotations


class IFCParserError(Exception):
    """Base exception for all IFC parser domain errors."""

    def __init__(self, message: str, code: str = "IFC_PARSER_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.module = "ifc_parser"

    def as_dict(self) -> dict[str, str]:
        return {
            "error_code": self.code,
            "module": self.module,
            "detail": self.message,
        }


class IFCFileNotFoundError(IFCParserError):
    """Raised when the specified IFC file does not exist on disk."""

    def __init__(self, detail: str) -> None:
        super().__init__(message=detail, code="IFC_FILE_NOT_FOUND")


class InvalidIFCFileError(IFCParserError):
    """Raised when the file is corrupt or not a valid STEP/IFC file."""

    def __init__(self, detail: str) -> None:
        super().__init__(message=detail, code="INVALID_IFC_FILE")


class UnsupportedIFCSchemaError(IFCParserError):
    """Raised when the IFC file schema is not supported (only IFC2X3, IFC4, IFC4X3 allowed)."""

    def __init__(self, detail: str) -> None:
        super().__init__(message=detail, code="UNSUPPORTED_IFC_SCHEMA")


class BuildingNotFoundError(IFCParserError):
    """Raised when no IfcBuilding entity is found in the model."""

    def __init__(self, detail: str = "No IfcBuilding entity found in the IFC model.") -> None:
        super().__init__(message=detail, code="BUILDING_NOT_FOUND")


class GeometryExtractionError(IFCParserError):
    """Raised when 3D bounding box or geometry extraction fails."""

    def __init__(self, detail: str) -> None:
        super().__init__(message=detail, code="GEOMETRY_EXTRACTION_ERROR")


class MetadataExtractionError(IFCParserError):
    """Raised when metadata extraction fails."""

    def __init__(self, detail: str) -> None:
        super().__init__(message=detail, code="METADATA_EXTRACTION_ERROR")


class StoreyExtractionError(IFCParserError):
    """Raised when storey hierarchy extraction fails."""

    def __init__(self, detail: str) -> None:
        super().__init__(message=detail, code="STOREY_EXTRACTION_ERROR")


class SpaceExtractionError(IFCParserError):
    """Raised when space extraction fails."""

    def __init__(self, detail: str) -> None:
        super().__init__(message=detail, code="SPACE_EXTRACTION_ERROR")


class StatisticsGenerationError(IFCParserError):
    """Raised when building statistics aggregation fails."""

    def __init__(self, detail: str) -> None:
        super().__init__(message=detail, code="STATISTICS_GENERATION_ERROR")
