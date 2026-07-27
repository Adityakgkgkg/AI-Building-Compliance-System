"""
AI Building Compliance System — IFC Parse Result Serializer

Assembles the canonical ParseResult from the three extractor outputs.
Validates through Pydantic before returning so downstream consumers
always receive a well-typed, schema-compliant object.
"""

from __future__ import annotations

import logging

from app.parser.schemas import BuildingInfo, ElementCounts, GeometryInfo, ParseResult

logger = logging.getLogger(__name__)


class ParseResultSerializer:
    """
    Assembles BuildingInfo + ElementCounts + GeometryInfo into ParseResult.

    This is intentionally a thin adapter — it converts the dict returned
    by ``extract_geometry()`` into a GeometryInfo Pydantic model and
    bundles everything into the canonical ParseResult.

    Usage:
        serializer = ParseResultSerializer()
        result = serializer.serialize(building, elements, geometry_dict)
    """

    def serialize(
        self,
        building: BuildingInfo,
        elements: ElementCounts,
        geometry_dict: dict,
    ) -> ParseResult:
        """
        Combine extractor outputs into a validated ParseResult.

        Args:
            building:      Populated BuildingInfo from MetadataExtractor.
            elements:      Populated ElementCounts from ElementExtractor.
            geometry_dict: Raw dict from utils.extract_geometry().

        Returns:
            ParseResult — Pydantic-validated canonical output.
        """
        geometry = self._build_geometry(geometry_dict)

        result = ParseResult(
            building=building,
            elements=elements,
            geometry=geometry,
        )

        logger.debug(
            "ParseResult assembled: schema=%s storeys=%d walls=%d",
            building.schema,
            building.storeys,
            elements.walls,
        )
        return result

    @staticmethod
    def _build_geometry(raw: dict) -> GeometryInfo:
        """
        Convert a raw geometry dict into a GeometryInfo model.

        Unknown keys are silently ignored; missing keys default to None
        via the GeometryInfo field defaults.
        """
        known_keys = {
            "gross_floor_area",
            "height",
            "storey_heights",
            "footprint",
            "bounding_box",
        }
        safe_dict = {k: v for k, v in raw.items() if k in known_keys}
        return GeometryInfo(**safe_dict)
