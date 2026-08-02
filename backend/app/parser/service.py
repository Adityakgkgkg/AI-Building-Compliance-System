"""
MCRDSE Module 1 – IFC Parser Service Layer
===========================================
``IFCParserService`` is the primary facade of the IFC Parser module.

Methods required by specifications & EvidenceCollector:
- ``parse()``
- ``extract_metadata()``
- ``extract_geometry()``
- ``extract_storeys()``
- ``extract_spaces()``
- ``extract_elements()``
- ``extract_statistics()``
- ``build_building_evidence()``
- ``parse_full()``
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

from app.parser.element_engine import IFCElementEngine
from app.parser.geometry_engine import IFCGeometryEngine
from app.parser.metadata_engine import IFCMetadataEngine
from app.parser.models import ParsedIFCRecord
from app.parser.parser_engine import IFCParserEngine
from app.parser.schemas import (
    IFCElementCount,
    IFCGeometry,
    IFCMetadata,
    IFCParseSummary,
    IFCSpace,
    IFCStatistics,
    IFCStorey,
    ParsedBuildingResult,
)
from app.parser.space_engine import IFCSpaceEngine
from app.parser.statistics_engine import IFCStatisticsEngine
from app.parser.storey_engine import IFCStoreyEngine
from app.parser.utils import elapsed_ms, generate_parse_id, perf_start, resolve_ifc_path, utc_now
from app.parser.validator import IFCValidator

logger = logging.getLogger("app.parser.service")


class IFCParserService:
    """
    Facade service orchestrating all IFC parsing engines.
    """

    @classmethod
    def parse(cls, ifc_file: str | Path) -> ParsedBuildingResult:
        """
        Primary entry point called by ``EvidenceCollector.collect_building()``.

        Parameters
        ----------
        ifc_file:
            Filename or Path of the IFC building plan.

        Returns
        -------
        ParsedBuildingResult
            Attribute-compatible payload mapped directly into BuildingEvidence.
        """
        return cls.build_building_evidence(ifc_file)

    @classmethod
    def build_building_evidence(cls, ifc_file: str | Path) -> ParsedBuildingResult:
        """
        Extract building attributes and return canonical ``ParsedBuildingResult``.
        """
        t0 = perf_start()
        file_path = resolve_ifc_path(ifc_file)
        model = IFCParserEngine.open_model(file_path)
        building = IFCValidator.validate_model(model)

        meta = IFCMetadataEngine.extract_metadata(model, building)
        geom = IFCGeometryEngine.extract_geometry(model, building)
        storeys = IFCStoreyEngine.extract_storeys(model)
        spaces = IFCSpaceEngine.extract_spaces(model)
        elements = IFCElementEngine.extract_element_counts(model)
        stats = IFCStatisticsEngine.generate_statistics(model, storeys, spaces, elements)

        ms = elapsed_ms(t0)
        logger.info(
            "IFC parsing completed | building_id=%s | height=%.2f m | elapsed=%.2f ms",
            meta.global_id,
            geom.building_height,
            ms,
        )

        return ParsedBuildingResult(
            building_id=meta.global_id,
            building_name=meta.building_name,
            building_type=meta.building_type,
            plot_area=stats.plot_area,
            builtup_area=stats.builtup_area,
            height=geom.building_height,
            floors=stats.floors,
            fsi=stats.fsi,
            ground_coverage=stats.ground_coverage,
            occupancy=meta.occupancy,
        )

    @classmethod
    def extract_metadata(cls, ifc_file: str | Path) -> IFCMetadata:
        """Extract IFCMetadata for a specified file."""
        file_path = resolve_ifc_path(ifc_file)
        model = IFCParserEngine.open_model(file_path)
        building = IFCValidator.validate_model(model)
        return IFCMetadataEngine.extract_metadata(model, building)

    @classmethod
    def extract_geometry(cls, ifc_file: str | Path) -> IFCGeometry:
        """Extract IFCGeometry for a specified file."""
        file_path = resolve_ifc_path(ifc_file)
        model = IFCParserEngine.open_model(file_path)
        building = IFCValidator.validate_model(model)
        return IFCGeometryEngine.extract_geometry(model, building)

    @classmethod
    def extract_storeys(cls, ifc_file: str | Path) -> List[IFCStorey]:
        """Extract list of IFCStorey for a specified file."""
        file_path = resolve_ifc_path(ifc_file)
        model = IFCParserEngine.open_model(file_path)
        return IFCStoreyEngine.extract_storeys(model)

    @classmethod
    def extract_spaces(cls, ifc_file: str | Path) -> List[IFCSpace]:
        """Extract list of IFCSpace for a specified file."""
        file_path = resolve_ifc_path(ifc_file)
        model = IFCParserEngine.open_model(file_path)
        return IFCSpaceEngine.extract_spaces(model)

    @classmethod
    def extract_elements(cls, ifc_file: str | Path) -> IFCElementCount:
        """Extract IFCElementCount for a specified file."""
        file_path = resolve_ifc_path(ifc_file)
        model = IFCParserEngine.open_model(file_path)
        return IFCElementEngine.extract_element_counts(model)

    @classmethod
    def extract_statistics(cls, ifc_file: str | Path) -> IFCStatistics:
        """Extract IFCStatistics for a specified file."""
        file_path = resolve_ifc_path(ifc_file)
        model = IFCParserEngine.open_model(file_path)
        storeys = IFCStoreyEngine.extract_storeys(model)
        spaces = IFCSpaceEngine.extract_spaces(model)
        elements = IFCElementEngine.extract_element_counts(model)
        return IFCStatisticsEngine.generate_statistics(model, storeys, spaces, elements)

    @classmethod
    def parse_full(cls, ifc_file: str | Path, db: Optional[object] = None) -> IFCParseSummary:
        """
        Perform full parsing run returning comprehensive ``IFCParseSummary``.
        """
        t0 = perf_start()
        parse_id = generate_parse_id()
        file_path = resolve_ifc_path(ifc_file)
        model = IFCParserEngine.open_model(file_path)
        building = IFCValidator.validate_model(model)

        meta = IFCMetadataEngine.extract_metadata(model, building)
        geom = IFCGeometryEngine.extract_geometry(model, building)
        storeys = IFCStoreyEngine.extract_storeys(model)
        spaces = IFCSpaceEngine.extract_spaces(model)
        elements = IFCElementEngine.extract_element_counts(model)
        stats = IFCStatisticsEngine.generate_statistics(model, storeys, spaces, elements)

        bld_result = ParsedBuildingResult(
            building_id=meta.global_id,
            building_name=meta.building_name,
            building_type=meta.building_type,
            plot_area=stats.plot_area,
            builtup_area=stats.builtup_area,
            height=geom.building_height,
            floors=stats.floors,
            fsi=stats.fsi,
            ground_coverage=stats.ground_coverage,
            occupancy=meta.occupancy,
        )

        ms = elapsed_ms(t0)

        # Audit logging to DB if session provided
        if db is not None:
            try:
                rec = ParsedIFCRecord(
                    parse_id=parse_id,
                    file_name=file_path.name,
                    ifc_schema=meta.schema_version,
                    building_id=meta.global_id,
                    building_name=meta.building_name,
                    building_type=meta.building_type,
                    floors=stats.floors,
                    height=geom.building_height,
                    builtup_area=stats.builtup_area,
                    plot_area=stats.plot_area,
                    fsi=stats.fsi,
                    ground_coverage=stats.ground_coverage,
                    parsed_at=utc_now(),
                    execution_time_ms=ms,
                )
                db.add(rec)  # type: ignore[union-attr]
                db.commit()  # type: ignore[union-attr]
            except Exception as exc:
                logger.error("Failed to persist ParsedIFCRecord | error=%s", exc)

        return IFCParseSummary(
            file_name=file_path.name,
            parse_id=parse_id,
            parsed_at=utc_now(),
            execution_time_ms=ms,
            building_evidence=bld_result,
            metadata=meta,
            geometry=geom,
            storeys=storeys,
            spaces=spaces,
            statistics=stats,
        )
