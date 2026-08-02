"""
MCRDSE Sprint 1 – Evidence Collector
======================================
``EvidenceCollector`` is the single orchestrator that calls each upstream
module, maps its output to the canonical schema, and assembles the
``EvidenceBundle``.

Architecture principles:
- **No recalculation**: every value is taken verbatim from an upstream module.
- **Adapter pattern**: upstream modules are resolved at runtime via helper
  methods so the collector remains forward-compatible as Modules 1 & 2 are
  completed.
- **Single Responsibility**: this class only collects and maps — no HTTP
  concerns, no persistence logic.
- **Structured failures**: each collector method raises a typed domain
  exception (from ``exceptions.py``) so callers get precise error context
  rather than bare ``Exception``.

Logging contract (per module spec):
    - ``Collection Start``  — logged before each upstream call
    - ``Collection Success``— logged after successful mapping
    - ``Collection Failure``— logged before re-raising a domain exception
    - ``Execution Time``    — logged in the success message
"""

from __future__ import annotations

import logging
from typing import List

from app.gis.context_engine import UrbanContextEngine
from app.gis.schemas import GISContextRequest, GISContextResponse
from app.report.exceptions import (
    BundleAssemblyError,
    ClassificationUnavailableError,
    ComplianceUnavailableError,
    GISUnavailableError,
    ParserUnavailableError,
)
from app.report.schemas import (
    BuildingEvidence,
    ClassificationEvidence,
    CollectionMetadata,
    ComplianceEvidence,
    DatasetProvenance,
    EvidenceBundle,
    GISEvidence,
    RuleResult,
)
from app.report.utils import elapsed_ms, generate_report_id, perf_start, utc_now

logger = logging.getLogger("app.report.evidence_collector")

# Module version sentinels — replaced by real version reads as modules ship.
_PARSER_VERSION = "0.0.0-stub"
_CLASSIFICATION_VERSION = "0.0.0-stub"
_GIS_ENGINE_VERSION = "1.0.0"
_COMPLIANCE_ENGINE_VERSION = "0.0.0-stub"


# ─────────────────────────────────────────────────────────────────────────────
# Private adapter resolution helpers
# ─────────────────────────────────────────────────────────────────────────────

def _resolve_parser_service():  # noqa: ANN201
    """
    Attempt to import the IFC Parser service.

    Returns the service class if the module is available.
    Raises :class:`ParserUnavailableError` if Module 1 is not yet implemented.
    """
    try:
        from app.parser.service import IFCParserService  # type: ignore[import-not-found]
        return IFCParserService
    except ModuleNotFoundError as exc:
        raise ParserUnavailableError(
            detail=(
                f"IFC Parser service module is not yet available "
                f"(app.parser.service not found): {exc}"
            )
        ) from exc


def _resolve_classification_service():  # noqa: ANN201
    """
    Attempt to import the Building Classification service.

    Returns the service class if the module is available.
    Raises :class:`ClassificationUnavailableError` if Module 2 is not yet implemented.
    """
    try:
        from app.compliance.classification.service import ClassificationService  # type: ignore[import-not-found]
        return ClassificationService
    except ModuleNotFoundError as exc:
        raise ClassificationUnavailableError(
            detail=(
                f"Building Classification service is not yet available "
                f"(app.compliance.classification.service not found): {exc}"
            )
        ) from exc


def _resolve_compliance_service():  # noqa: ANN201
    """
    Attempt to import the Compliance Engine service.

    Returns the service class if the module is available.
    Raises :class:`ComplianceUnavailableError` if the engine is not yet implemented.
    """
    try:
        from app.compliance.rule_engine.service import ComplianceEngineService  # type: ignore[import-not-found]
        return ComplianceEngineService
    except ModuleNotFoundError as exc:
        raise ComplianceUnavailableError(
            detail=(
                f"Compliance Engine service is not yet available "
                f"(app.compliance.rule_engine.service not found): {exc}"
            )
        ) from exc


# ─────────────────────────────────────────────────────────────────────────────
# GIS mapping helpers (pure projection — no computation)
# ─────────────────────────────────────────────────────────────────────────────

def _map_gis_response_to_evidence(gis_response: GISContextResponse) -> GISEvidence:
    """
    Project a :class:`GISContextResponse` onto :class:`GISEvidence`.

    This is a pure field-to-field mapping.  No spatial logic runs here.
    The ``dataset_manifest`` is built from the ``citations`` list carried by
    the GIS response.

    Parameters
    ----------
    gis_response:
        Full urban context response from the GIS Context Engine.

    Returns
    -------
    GISEvidence
        Canonical evidence object populated from the GIS response.
    """
    manifest: List[DatasetProvenance] = [
        DatasetProvenance(
            dataset_name=cit.dataset_name,
            authority=cit.authority,
            source_url=cit.source_url,
            license=cit.license,
            feature_id=cit.feature_id,
            observation=cit.observation,
        )
        for cit in gis_response.citations
    ]

    return GISEvidence(
        authority=gis_response.authority,
        ward=gis_response.ward,
        ward_number=gis_response.ward_number,
        zone=gis_response.zone,
        road_name=gis_response.road_name,
        road_width=gis_response.road_width,
        land_use=gis_response.land_use,
        lake_distance=gis_response.lake_distance,
        lake_buffer=gis_response.lake_buffer,
        airport_zone=gis_response.airport_zone,
        airport_height_limit=gis_response.airport_height_limit,
        flood_risk=gis_response.flood_risk,
        heritage_zone=gis_response.heritage_zone,
        dataset_manifest=manifest,
    )


# ─────────────────────────────────────────────────────────────────────────────
# EvidenceCollector — main orchestrator
# ─────────────────────────────────────────────────────────────────────────────

class EvidenceCollector:
    """
    Orchestrates evidence collection from all upstream compliance modules.

    Each ``collect_*`` method:
    1. Calls the corresponding upstream module service.
    2. Maps the response to the canonical schema.
    3. Logs start, success (with timing), or failure before re-raising.

    :meth:`build_bundle` composes all four collectors into an
    :class:`EvidenceBundle`.
    """

    # ── Public collection interface ───────────────────────────────────────────

    def collect_building(self, ifc_file: str) -> BuildingEvidence:
        """
        Collect IFC-parsed building metadata from Module 1.

        Parameters
        ----------
        ifc_file:
            Filename of the uploaded IFC file to parse.

        Returns
        -------
        BuildingEvidence
            Canonical building metadata mapped from the IFC Parser output.

        Raises
        ------
        ParserUnavailableError
            If Module 1 (IFC Parser) service cannot be resolved or fails.
        """
        logger.info("[Collection Start] IFC Parser | ifc_file=%s", ifc_file)
        t0 = perf_start()

        try:
            parser_service = _resolve_parser_service()
            raw = parser_service.parse(ifc_file)
            evidence = BuildingEvidence(
                building_id=raw.building_id,
                building_name=raw.building_name,
                ifc_file=ifc_file,
                building_type=raw.building_type,
                plot_area=raw.plot_area,
                builtup_area=raw.builtup_area,
                height=raw.height,
                floors=raw.floors,
                fsi=raw.fsi,
                ground_coverage=raw.ground_coverage,
                occupancy=raw.occupancy,
            )
        except ParserUnavailableError:
            ms = elapsed_ms(t0)
            logger.warning(
                "[Collection Failure] IFC Parser unavailable | elapsed=%.2f ms", ms
            )
            raise
        except Exception as exc:
            ms = elapsed_ms(t0)
            logger.error(
                "[Collection Failure] IFC Parser raised unexpected error | "
                "elapsed=%.2f ms | error=%s",
                ms,
                exc,
            )
            raise ParserUnavailableError(
                detail=f"IFC Parser returned an unexpected error: {exc}"
            ) from exc

        ms = elapsed_ms(t0)
        logger.info(
            "[Collection Success] IFC Parser | building_id=%s | elapsed=%.2f ms",
            evidence.building_id,
            ms,
        )
        return evidence

    def collect_classification(
        self, building_ev: BuildingEvidence
    ) -> ClassificationEvidence:
        """
        Collect building type classification from Module 2.

        Parameters
        ----------
        building_ev:
            Previously collected building evidence (used as input to the
            classifier).

        Returns
        -------
        ClassificationEvidence
            Canonical classification evidence mapped from the classifier output.

        Raises
        ------
        ClassificationUnavailableError
            If Module 2 (Building Classification) service cannot be resolved
            or fails.
        """
        logger.info(
            "[Collection Start] Building Classification | building_id=%s",
            building_ev.building_id,
        )
        t0 = perf_start()

        try:
            classification_service = _resolve_classification_service()
            raw = classification_service.classify(building_ev)
            evidence = ClassificationEvidence(
                predicted_type=raw.predicted_type,
                confidence=raw.confidence,
                reason=raw.reason,
            )
        except ClassificationUnavailableError:
            ms = elapsed_ms(t0)
            logger.warning(
                "[Collection Failure] Classification unavailable | elapsed=%.2f ms", ms
            )
            raise
        except Exception as exc:
            ms = elapsed_ms(t0)
            logger.error(
                "[Collection Failure] Classification raised unexpected error | "
                "elapsed=%.2f ms | error=%s",
                ms,
                exc,
            )
            raise ClassificationUnavailableError(
                detail=f"Building Classification returned an unexpected error: {exc}"
            ) from exc

        ms = elapsed_ms(t0)
        logger.info(
            "[Collection Success] Building Classification | type=%s confidence=%.3f | elapsed=%.2f ms",
            evidence.predicted_type,
            evidence.confidence,
            ms,
        )
        return evidence

    def collect_gis(self, lat: float, lon: float) -> GISEvidence:
        """
        Collect urban spatial context from the GIS Context Engine (Module 3).

        This is the only upstream module fully implemented in this sprint.
        The method calls :class:`UrbanContextEngine` directly and projects its
        rich :class:`GISContextResponse` onto the canonical :class:`GISEvidence`
        schema.

        Parameters
        ----------
        lat:
            WGS84 latitude of the building site.
        lon:
            WGS84 longitude of the building site.

        Returns
        -------
        GISEvidence
            Canonical GIS evidence projected from the GIS Context Engine output.

        Raises
        ------
        GISUnavailableError
            If the GIS Context Engine raises an unexpected error.
        """
        logger.info(
            "[Collection Start] GIS Context Engine | lat=%.6f lon=%.6f", lat, lon
        )
        t0 = perf_start()

        try:
            request = GISContextRequest(latitude=lat, longitude=lon)
            gis_response: GISContextResponse = UrbanContextEngine.evaluate_context(request)
            evidence = _map_gis_response_to_evidence(gis_response)
        except GISUnavailableError:
            ms = elapsed_ms(t0)
            logger.warning(
                "[Collection Failure] GIS Context Engine unavailable | elapsed=%.2f ms", ms
            )
            raise
        except Exception as exc:
            ms = elapsed_ms(t0)
            logger.error(
                "[Collection Failure] GIS Context Engine raised unexpected error | "
                "elapsed=%.2f ms | error=%s",
                ms,
                exc,
            )
            raise GISUnavailableError(
                detail=f"GIS Context Engine returned an unexpected error: {exc}"
            ) from exc

        ms = elapsed_ms(t0)
        logger.info(
            "[Collection Success] GIS Context Engine | ward=%s zone=%s | elapsed=%.2f ms",
            evidence.ward,
            evidence.zone,
            ms,
        )
        return evidence

    def collect_compliance(
        self,
        building_ev: BuildingEvidence,
        gis_ev: GISEvidence,
    ) -> ComplianceEvidence:
        """
        Collect rule evaluation results from the Compliance Engine (Module 2).

        Parameters
        ----------
        building_ev:
            Canonical building evidence used as compliance input.
        gis_ev:
            Canonical GIS evidence used as compliance input.

        Returns
        -------
        ComplianceEvidence
            Canonical compliance evidence mapped from the engine output.

        Raises
        ------
        ComplianceUnavailableError
            If the Compliance Engine service cannot be resolved or fails.
        """
        logger.info(
            "[Collection Start] Compliance Engine | building_id=%s",
            building_ev.building_id,
        )
        t0 = perf_start()

        try:
            compliance_service = _resolve_compliance_service()
            raw = compliance_service.evaluate(building_ev, gis_ev)

            rule_results: List[RuleResult] = [
                RuleResult(
                    rule_id=r.rule_id,
                    rule_name=r.rule_name,
                    status=r.status,
                    severity=r.severity,
                    expected=r.expected,
                    actual=r.actual,
                    difference=r.difference,
                    message=r.message,
                    clause=r.clause,
                    reference=r.reference,
                    recommendation=r.recommendation,
                )
                for r in raw.rule_results
            ]

            evidence = ComplianceEvidence(
                rules_checked=raw.rules_checked,
                passed=raw.passed,
                failed=raw.failed,
                warnings=raw.warnings,
                blocking=raw.blocking,
                score=raw.score,
                rule_results=rule_results,
            )
        except ComplianceUnavailableError:
            ms = elapsed_ms(t0)
            logger.warning(
                "[Collection Failure] Compliance Engine unavailable | elapsed=%.2f ms", ms
            )
            raise
        except Exception as exc:
            ms = elapsed_ms(t0)
            logger.error(
                "[Collection Failure] Compliance Engine raised unexpected error | "
                "elapsed=%.2f ms | error=%s",
                ms,
                exc,
            )
            raise ComplianceUnavailableError(
                detail=f"Compliance Engine returned an unexpected error: {exc}"
            ) from exc

        ms = elapsed_ms(t0)
        logger.info(
            "[Collection Success] Compliance Engine | score=%.1f rules=%d | elapsed=%.2f ms",
            evidence.score,
            evidence.rules_checked,
            ms,
        )
        return evidence

    def build_bundle(
        self,
        ifc_file: str,
        lat: float,
        lon: float,
    ) -> EvidenceBundle:
        """
        Orchestrate all evidence collectors and assemble the canonical
        :class:`EvidenceBundle`.

        Execution order:
        1. :meth:`collect_building` — IFC Parser (Module 1)
        2. :meth:`collect_classification` — Building Classifier (Module 2)
        3. :meth:`collect_gis` — GIS Context Engine (Module 3)
        4. :meth:`collect_compliance` — Compliance Engine (Module 2)

        Steps 3 and 4 are independent of 1 & 2 at the data level, but the
        compliance engine requires building and GIS data as inputs, so the
        sequential order is maintained.

        Parameters
        ----------
        ifc_file:
            Filename of the uploaded IFC file.
        lat:
            WGS84 latitude of the building site.
        lon:
            WGS84 longitude of the building site.

        Returns
        -------
        EvidenceBundle
            Fully assembled canonical evidence bundle.

        Raises
        ------
        ParserUnavailableError
            If the IFC Parser module is unavailable.
        ClassificationUnavailableError
            If the Building Classification module is unavailable.
        GISUnavailableError
            If the GIS Context Engine is unavailable.
        ComplianceUnavailableError
            If the Compliance Engine is unavailable.
        BundleAssemblyError
            If an unexpected error occurs during final bundle construction.
        """
        bundle_start = perf_start()
        report_id = generate_report_id()
        timestamp = utc_now()

        logger.info(
            "[Collection Start] EvidenceBundle | report_id=%s ifc_file=%s lat=%.6f lon=%.6f",
            report_id,
            ifc_file,
            lat,
            lon,
        )

        # ── Step 1: IFC Parser ────────────────────────────────────────────────
        t_building = perf_start()
        building_ev = self.collect_building(ifc_file)
        building_ms = elapsed_ms(t_building)

        # ── Step 2: Building Classification ──────────────────────────────────
        t_classification = perf_start()
        classification_ev = self.collect_classification(building_ev)
        classification_ms = elapsed_ms(t_classification)

        # ── Step 3: GIS Context Engine ────────────────────────────────────────
        t_gis = perf_start()
        gis_ev = self.collect_gis(lat, lon)
        gis_ms = elapsed_ms(t_gis)

        # ── Step 4: Compliance Engine ─────────────────────────────────────────
        t_compliance = perf_start()
        compliance_ev = self.collect_compliance(building_ev, gis_ev)
        compliance_ms = elapsed_ms(t_compliance)

        # ── Assemble bundle ───────────────────────────────────────────────────
        total_ms = elapsed_ms(bundle_start)

        try:
            from app.core.config import get_settings  # local import avoids circular deps
            software_version = get_settings().APP_VERSION
        except Exception:
            software_version = "unknown"

        metadata = CollectionMetadata(
            collected_at=utc_now(),
            building_collection_ms=building_ms,
            classification_collection_ms=classification_ms,
            gis_collection_ms=gis_ms,
            compliance_collection_ms=compliance_ms,
            total_collection_ms=total_ms,
            ifc_parser_version=_PARSER_VERSION,
            classification_version=_CLASSIFICATION_VERSION,
            gis_engine_version=_GIS_ENGINE_VERSION,
            compliance_engine_version=_COMPLIANCE_ENGINE_VERSION,
        )

        try:
            bundle = EvidenceBundle(
                report_id=report_id,
                timestamp=timestamp,
                building=building_ev,
                classification=classification_ev,
                gis=gis_ev,
                compliance=compliance_ev,
                metadata=metadata,
                software_version=software_version,
            )
        except Exception as exc:
            logger.error(
                "[Collection Failure] Bundle assembly failed | report_id=%s | error=%s",
                report_id,
                exc,
            )
            raise BundleAssemblyError(
                detail=f"EvidenceBundle construction failed: {exc}"
            ) from exc

        logger.info(
            "[Collection Success] EvidenceBundle assembled | report_id=%s | "
            "gis_ward=%s | total_elapsed=%.2f ms",
            report_id,
            gis_ev.ward,
            total_ms,
        )
        return bundle
