"""
AI Building Compliance System — IFC Metadata Extractor

Extracts project, building, site, schema, and owner metadata
from an open IfcOpenShell model. All attribute access is performed
through safe_get() so missing or null properties return gracefully.
"""

from __future__ import annotations

import logging
from typing import Any

from app.parser.schemas import BuildingInfo
from app.parser.utils import get_length_unit, safe_get

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """
    Extracts building metadata from an IfcOpenShell model.

    Usage:
        extractor = MetadataExtractor()
        info = extractor.extract(ifc_model)
    """

    def extract(self, ifc_model: Any) -> BuildingInfo:
        """
        Parse the IFC model and return a populated BuildingInfo.

        Extracts:
            - Project name (IfcProject.Name)
            - Building name (IfcBuilding.Name)
            - Site name (IfcSite.Name)
            - Building description (IfcBuilding.Description)
            - Schema version (ifc_model.schema)
            - Number of storeys (count of IfcBuildingStorey)
            - Length unit (IfcUnitAssignment)
            - Owner organization (IfcOwnerHistory)

        Args:
            ifc_model: An open ifcopenshell.file instance.

        Returns:
            BuildingInfo with all available fields populated.
        """
        logger.debug("Extracting building metadata…")

        project_name = self._extract_project_name(ifc_model)
        building_name, description = self._extract_building_info(ifc_model)
        site_name = self._extract_site_name(ifc_model)
        schema = self._extract_schema(ifc_model)
        storeys = self._count_storeys(ifc_model)
        units = self._extract_units(ifc_model)
        owner = self._extract_owner(ifc_model)

        info = BuildingInfo(
            project_name=project_name,
            building_name=building_name,
            site_name=site_name,
            description=description,
            ifc_schema=schema,
            storeys=storeys,
            units=units,
            owner=owner,
        )

        logger.info(
            "Metadata extracted: project='%s' building='%s' schema=%s storeys=%d",
            project_name,
            building_name,
            schema,
            storeys,
        )
        return info

    # ── Private extraction methods ────────────────────────────────

    @staticmethod
    def _extract_project_name(ifc_model: Any) -> str | None:
        """Extract Name from the first IfcProject entity."""
        try:
            projects = ifc_model.by_type("IfcProject")
            if projects:
                return safe_get(projects[0], "Name") or None
        except Exception as exc:
            logger.debug("IfcProject name extraction failed: %s", exc)
        return None

    @staticmethod
    def _extract_building_info(ifc_model: Any) -> tuple[str | None, str | None]:
        """
        Extract Name and Description from the first IfcBuilding entity.

        Returns:
            (building_name, description) — either may be None.
        """
        try:
            buildings = ifc_model.by_type("IfcBuilding")
            if buildings:
                building = buildings[0]
                name = safe_get(building, "Name") or None
                desc = safe_get(building, "Description") or None
                return name, desc
        except Exception as exc:
            logger.debug("IfcBuilding info extraction failed: %s", exc)
        return None, None

    @staticmethod
    def _extract_site_name(ifc_model: Any) -> str | None:
        """Extract Name from the first IfcSite entity."""
        try:
            sites = ifc_model.by_type("IfcSite")
            if sites:
                return safe_get(sites[0], "Name") or None
        except Exception as exc:
            logger.debug("IfcSite name extraction failed: %s", exc)
        return None

    @staticmethod
    def _extract_schema(ifc_model: Any) -> str | None:
        """Read the schema version string from the IFC model."""
        try:
            schema = getattr(ifc_model, "schema", None)
            return str(schema).upper() if schema else None
        except Exception as exc:
            logger.debug("Schema extraction failed: %s", exc)
        return None

    @staticmethod
    def _count_storeys(ifc_model: Any) -> int:
        """Count IfcBuildingStorey entities in the model."""
        try:
            storeys = ifc_model.by_type("IfcBuildingStorey")
            return len(storeys)
        except Exception as exc:
            logger.debug("Storey count failed: %s", exc)
        return 0

    @staticmethod
    def _extract_units(ifc_model: Any) -> str | None:
        """Return the primary length unit name."""
        try:
            return get_length_unit(ifc_model)
        except Exception as exc:
            logger.debug("Unit extraction failed: %s", exc)
        return None

    @staticmethod
    def _extract_owner(ifc_model: Any) -> str | None:
        """
        Extract the owning organization name from IfcOwnerHistory.

        Traversal: IfcOwnerHistory → OwningOrganization → Name
        """
        try:
            histories = ifc_model.by_type("IfcOwnerHistory")
            if histories:
                org_name = safe_get(
                    histories[0], "OwningOrganization", "Name"
                )
                if org_name:
                    return str(org_name)
                # Fallback: try OwningUser → ThePerson → FamilyName
                person_name = safe_get(
                    histories[0], "OwningUser", "ThePerson", "FamilyName"
                )
                if person_name:
                    return str(person_name)
        except Exception as exc:
            logger.debug("Owner extraction failed: %s", exc)
        return None
