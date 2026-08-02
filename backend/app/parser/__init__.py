"""
MCRDSE Module 1 – IFC Parser Engine Package
============================================
Public exports for app.parser package.
"""

from app.parser.exceptions import (
    BuildingNotFoundError,
    GeometryExtractionError,
    IFCFileNotFoundError,
    IFCParserError,
    InvalidIFCFileError,
    MetadataExtractionError,
    SpaceExtractionError,
    StatisticsGenerationError,
    StoreyExtractionError,
    UnsupportedIFCSchemaError,
)
from app.parser.parser_engine import IFCParserEngine
from app.parser.router import router as parser_router
from app.parser.schemas import ParsedBuildingResult
from app.parser.service import IFCParserService

__all__ = [
    "BuildingNotFoundError",
    "GeometryExtractionError",
    "IFCFileNotFoundError",
    "IFCParserEngine",
    "IFCParserError",
    "IFCParserService",
    "InvalidIFCFileError",
    "MetadataExtractionError",
    "ParsedBuildingResult",
    "SpaceExtractionError",
    "StatisticsGenerationError",
    "StoreyExtractionError",
    "UnsupportedIFCSchemaError",
    "parser_router",
]
