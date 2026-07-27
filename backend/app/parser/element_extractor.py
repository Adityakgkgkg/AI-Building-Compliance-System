"""
AI Building Compliance System — IFC Element Extractor

Counts building elements by IFC type using ifc_model.by_type().
Returns ElementCounts with zero defaults for any type not present
in the model — never raises an exception.
"""

from __future__ import annotations

import logging
from typing import Any

from app.parser.schemas import ElementCounts

logger = logging.getLogger(__name__)

# Map of ElementCounts field name → IFC entity type name
_ELEMENT_TYPE_MAP: dict[str, str] = {
    "walls": "IfcWall",
    "doors": "IfcDoor",
    "windows": "IfcWindow",
    "slabs": "IfcSlab",
    "columns": "IfcColumn",
    "beams": "IfcBeam",
    "roofs": "IfcRoof",
    "stairs": "IfcStair",
    "spaces": "IfcSpace",
    "openings": "IfcOpeningElement",
}


class ElementExtractor:
    """
    Counts IFC building element entities by type.

    Iterates over ``_ELEMENT_TYPE_MAP`` and calls
    ``ifc_model.by_type(type_name)`` for each entry.
    Counts include subtypes (IfcOpenShell default behaviour).

    Usage:
        extractor = ElementExtractor()
        counts = extractor.extract(ifc_model)
    """

    def extract(self, ifc_model: Any) -> ElementCounts:
        """
        Count all recognised element types in *ifc_model*.

        Args:
            ifc_model: An open ifcopenshell.file instance.

        Returns:
            ElementCounts with integer totals for each type.
            Missing types default to 0.
        """
        logger.debug("Extracting element counts…")
        counts: dict[str, int] = {}

        for field_name, ifc_type in _ELEMENT_TYPE_MAP.items():
            counts[field_name] = self._count_type(ifc_model, ifc_type)

        element_counts = ElementCounts(**counts)
        logger.info(
            "Element counts extracted: walls=%d doors=%d windows=%d slabs=%d "
            "columns=%d beams=%d roofs=%d stairs=%d spaces=%d openings=%d",
            element_counts.walls,
            element_counts.doors,
            element_counts.windows,
            element_counts.slabs,
            element_counts.columns,
            element_counts.beams,
            element_counts.roofs,
            element_counts.stairs,
            element_counts.spaces,
            element_counts.openings,
        )
        return element_counts

    @staticmethod
    def _count_type(ifc_model: Any, ifc_type: str) -> int:
        """
        Return the count of *ifc_type* entities in the model.

        Returns 0 if the type does not exist or any error occurs.
        """
        try:
            entities = ifc_model.by_type(ifc_type)
            return len(entities)
        except Exception as exc:
            logger.debug("Could not count '%s': %s", ifc_type, exc)
            return 0
