"""
MCRDSE Sprint 1 – Evidence Collection Layer Unit & Integration Tests
====================================================================
Test coverage:

1.  Schema validation — ``EvidenceBundle`` construction with correct types.
2.  ``collect_gis()`` — calls real GIS engine and maps to ``GISEvidence``.
3.  ``collect_building()`` — raises ``ParserUnavailableError`` (Module 1 stub).
4.  ``collect_compliance()`` — raises ``ComplianceUnavailableError`` (stub).
5.  ``collect_classification()`` — raises ``ClassificationUnavailableError`` (stub).
6.  ``build_bundle()`` — surfaces correct exception when an upstream module is absent.
7.  ``ReportService.collect_evidence()`` — returns ``(ModuleErrorDetail, 503)`` tuple.
8.  GET ``/api/v1/report/context`` — HTTP 200 with valid schema (GIS-only mock).
9.  GET ``/api/v1/report/context`` — HTTP 503 structured error when module absent.
10. Performance — GIS-only collection completes within 2 000 ms ceiling.
11. Utility functions — ``generate_report_id``, ``utc_now``, ``elapsed_ms``.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import List
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ── Application bootstrap ─────────────────────────────────────────────────────
from main import app
from app.gis.dataset_manager import DatasetManager
from app.gis.context_engine import UrbanContextEngine
from app.gis.schemas import GISContextRequest

# ── Module under test ─────────────────────────────────────────────────────────
from app.report.evidence_collector import EvidenceCollector
from app.report.exceptions import (
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
    ModuleErrorDetail,
    RuleResult,
)
from app.report.service import ReportService
from app.report.utils import elapsed_ms, generate_report_id, perf_start, utc_now


# ─────────────────────────────────────────────────────────────────────────────
# Test constants
# ─────────────────────────────────────────────────────────────────────────────
_JAYANAGAR_LAT = 12.9250
_JAYANAGAR_LON = 77.5938
_TEST_IFC = "test_building.ifc"


# ─────────────────────────────────────────────────────────────────────────────
# Session-scoped fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    """FastAPI test client with GIS datasets pre-loaded."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module", autouse=True)
def setup_gis():
    """Initialise GIS datasets once for the entire test session."""
    dm = DatasetManager.get_instance()
    dm.initialize()


# ─────────────────────────────────────────────────────────────────────────────
# Helper factories (build valid canonical objects without upstream modules)
# ─────────────────────────────────────────────────────────────────────────────

def _make_building_evidence(ifc_file: str = _TEST_IFC) -> BuildingEvidence:
    """Construct a minimal valid BuildingEvidence for testing."""
    return BuildingEvidence(
        building_id="test-building-001",
        building_name="Test Residential Building",
        ifc_file=ifc_file,
        building_type="RESIDENTIAL",
        plot_area=450.0,
        builtup_area=810.0,
        height=12.5,
        floors=3,
        fsi=1.8,
        ground_coverage=40.0,
        occupancy="Residential",
    )


def _make_classification_evidence() -> ClassificationEvidence:
    """Construct a minimal valid ClassificationEvidence for testing."""
    return ClassificationEvidence(
        predicted_type="Residential",
        confidence=0.95,
        reason="Floor count and occupancy strongly indicate residential use.",
    )


def _make_gis_evidence() -> GISEvidence:
    """Construct a minimal valid GISEvidence for testing."""
    return GISEvidence(
        authority="BBMP",
        ward="Jayanagar",
        ward_number=167,
        zone="South Zone",
        road_name="11th Main Road",
        road_width=12.0,
        land_use="Residential",
        lake_distance=500.0,
        lake_buffer=False,
        airport_zone=False,
        airport_height_limit=None,
        flood_risk="Low",
        heritage_zone=False,
        dataset_manifest=[
            DatasetProvenance(
                dataset_name="BBMP Ward Boundaries",
                authority="BBMP / DataMeet",
                source_url="https://projects.datameet.org/Municipal_Spatial_Data/bangalore/",
                license="ODbL / Creative Commons BY-SA",
                feature_id="ward_167",
                observation="Site falls within Jayanagar Ward 167.",
            )
        ],
    )


def _make_rule_result(
    rule_id: str = "BBMP-FSI-001",
    status: str = "PASSED",
    severity: str = "MAJOR",
) -> RuleResult:
    return RuleResult(
        rule_id=rule_id,
        rule_name="FSI Compliance Check",
        status=status,
        severity=severity,
        expected="≤ 2.25",
        actual="1.80",
        difference="−0.45 (within limit)",
        message="FSI is within the permitted limit for South Zone residential.",
        clause="BBMP Bye-law 7.3.2",
        reference="BBMP Building Bye-laws 2024, §7",
        recommendation="No corrective action required.",
    )


def _make_compliance_evidence() -> ComplianceEvidence:
    return ComplianceEvidence(
        rules_checked=5,
        passed=4,
        failed=0,
        warnings=1,
        blocking=0,
        score=92.0,
        rule_results=[_make_rule_result()],
    )


def _make_collection_metadata() -> CollectionMetadata:
    return CollectionMetadata(
        collected_at=datetime.now(timezone.utc),
        building_collection_ms=12.5,
        classification_collection_ms=8.3,
        gis_collection_ms=45.7,
        compliance_collection_ms=20.1,
        total_collection_ms=90.0,
        ifc_parser_version="0.0.0-stub",
        classification_version="0.0.0-stub",
        gis_engine_version="1.0.0",
        compliance_engine_version="0.0.0-stub",
    )


def _make_evidence_bundle() -> EvidenceBundle:
    """Construct a fully valid EvidenceBundle from fixture data."""
    return EvidenceBundle(
        report_id=generate_report_id(),
        timestamp=datetime.now(timezone.utc),
        building=_make_building_evidence(),
        classification=_make_classification_evidence(),
        gis=_make_gis_evidence(),
        compliance=_make_compliance_evidence(),
        metadata=_make_collection_metadata(),
        software_version="0.1.0",
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1. Schema validation tests
# ─────────────────────────────────────────────────────────────────────────────

class TestSchemaValidation:
    """Validate Pydantic v2 schema construction and field constraints."""

    def test_evidence_bundle_construction(self):
        """EvidenceBundle constructs without error from valid fixture data."""
        bundle = _make_evidence_bundle()
        assert isinstance(bundle, EvidenceBundle)
        assert bundle.report_id  # non-empty
        assert isinstance(bundle.timestamp, datetime)
        assert bundle.timestamp.tzinfo is not None, "timestamp must be timezone-aware"

    def test_report_id_is_uuid4(self):
        """report_id must be a valid UUID4 string."""
        bundle = _make_evidence_bundle()
        parsed = uuid.UUID(bundle.report_id, version=4)
        assert str(parsed) == bundle.report_id

    def test_building_evidence_field_types(self):
        """All BuildingEvidence fields must have correct Python types."""
        be = _make_building_evidence()
        assert isinstance(be.building_id, str)
        assert isinstance(be.plot_area, float)
        assert isinstance(be.builtup_area, float)
        assert isinstance(be.floors, int)
        assert isinstance(be.fsi, float)
        assert isinstance(be.ground_coverage, float)

    def test_gis_evidence_dataset_manifest_type(self):
        """dataset_manifest must be a list of DatasetProvenance instances."""
        ge = _make_gis_evidence()
        assert isinstance(ge.dataset_manifest, list)
        assert all(isinstance(p, DatasetProvenance) for p in ge.dataset_manifest)

    def test_compliance_evidence_score_range(self):
        """Compliance score must be in [0.0, 100.0]."""
        ce = _make_compliance_evidence()
        assert 0.0 <= ce.score <= 100.0

    def test_rule_result_all_required_fields_present(self):
        """Every RuleResult field specified in the requirements must be populated."""
        rr = _make_rule_result()
        required_fields = [
            "rule_id", "rule_name", "status", "severity",
            "expected", "actual", "difference", "message",
            "clause", "reference", "recommendation",
        ]
        for field in required_fields:
            assert getattr(rr, field) != "", f"RuleResult.{field} must not be empty"

    def test_classification_confidence_bounds(self):
        """Confidence must be in [0.0, 1.0]."""
        ce = _make_classification_evidence()
        assert 0.0 <= ce.confidence <= 1.0

    def test_module_error_detail_fields(self):
        """ModuleErrorDetail must carry error_code, module, and detail."""
        err = ModuleErrorDetail(
            error_code="PARSER_MODULE_UNAVAILABLE",
            module="ifc_parser",
            detail="IFC Parser module is not yet available.",
        )
        assert err.error_code == "PARSER_MODULE_UNAVAILABLE"
        assert err.module == "ifc_parser"
        assert err.detail

    def test_bundle_is_immutable(self):
        """EvidenceBundle is frozen — mutation must raise an error."""
        bundle = _make_evidence_bundle()
        with pytest.raises(Exception):
            bundle.software_version = "99.0.0"  # type: ignore[misc]

    def test_bundle_json_serialisable(self):
        """EvidenceBundle.model_dump(mode='json') must produce a plain dict."""
        import json
        bundle = _make_evidence_bundle()
        data = bundle.model_dump(mode="json")
        json_str = json.dumps(data)
        assert isinstance(json_str, str) and len(json_str) > 100


# ─────────────────────────────────────────────────────────────────────────────
# 2. collect_gis() — live GIS module integration
# ─────────────────────────────────────────────────────────────────────────────

class TestCollectGIS:
    """Integration tests calling the real GIS Context Engine."""

    def test_collect_gis_returns_gis_evidence(self):
        """collect_gis() must return a GISEvidence instance."""
        collector = EvidenceCollector()
        evidence = collector.collect_gis(_JAYANAGAR_LAT, _JAYANAGAR_LON)
        assert isinstance(evidence, GISEvidence)

    def test_collect_gis_authority_is_bbmp(self):
        """GIS evidence authority must be 'BBMP' for Jayanagar coordinates."""
        collector = EvidenceCollector()
        evidence = collector.collect_gis(_JAYANAGAR_LAT, _JAYANAGAR_LON)
        assert evidence.authority == "BBMP"

    def test_collect_gis_ward_name_non_empty(self):
        """Ward name must be a non-empty string."""
        collector = EvidenceCollector()
        evidence = collector.collect_gis(_JAYANAGAR_LAT, _JAYANAGAR_LON)
        assert isinstance(evidence.ward, str) and len(evidence.ward) > 0

    def test_collect_gis_road_width_positive(self):
        """Road width must be positive."""
        collector = EvidenceCollector()
        evidence = collector.collect_gis(_JAYANAGAR_LAT, _JAYANAGAR_LON)
        assert evidence.road_width > 0.0

    def test_collect_gis_flood_risk_valid_enum(self):
        """Flood risk must be one of the permitted values."""
        collector = EvidenceCollector()
        evidence = collector.collect_gis(_JAYANAGAR_LAT, _JAYANAGAR_LON)
        assert evidence.flood_risk in {"Low", "Medium", "High"}

    def test_collect_building_raises_parser_unavailable(self):
        with pytest.raises(ParserUnavailableError) as exc_info:
            collector = EvidenceCollector()
            collector.collect_building(ifc_file="non_existent_file_xyz_999.ifc")

        assert exc_info.value.code == "PARSER_MODULE_UNAVAILABLE"
        assert "not found" in exc_info.value.message.lower()

    def test_collect_building_error_as_dict(self):
        with pytest.raises(ParserUnavailableError) as exc_info:
            collector = EvidenceCollector()
            collector.collect_building(ifc_file="non_existent_file_xyz_999.ifc")

        d = exc_info.value.as_dict()
        assert d["error_code"] == "PARSER_MODULE_UNAVAILABLE"
        assert d["module"] == "ifc_parser"

    def test_collect_gis_dataset_manifest_non_empty(self):
        """Dataset manifest must contain at least one provenance entry."""
        collector = EvidenceCollector()
        evidence = collector.collect_gis(_JAYANAGAR_LAT, _JAYANAGAR_LON)
        assert len(evidence.dataset_manifest) > 0
        first = evidence.dataset_manifest[0]
        assert isinstance(first, DatasetProvenance)
        assert first.authority
        assert first.source_url

    def test_collect_gis_lake_distance_non_negative(self):
        """Lake distance must be >= 0."""
        collector = EvidenceCollector()
        evidence = collector.collect_gis(_JAYANAGAR_LAT, _JAYANAGAR_LON)
        assert evidence.lake_distance >= 0.0

    def test_collect_gis_raises_on_engine_error(self):
        """collect_gis() must raise GISUnavailableError when engine throws."""
        collector = EvidenceCollector()
        with patch.object(
            UrbanContextEngine,
            "evaluate_context",
            side_effect=RuntimeError("GIS engine exploded"),
        ):
            with pytest.raises(GISUnavailableError) as exc_info:
                collector.collect_gis(_JAYANAGAR_LAT, _JAYANAGAR_LON)
        assert "GIS engine exploded" in str(exc_info.value)


# ─────────────────────────────────────────────────────────────────────────────
# 3. collect_building() — Module 1 stub handling
# ─────────────────────────────────────────────────────────────────────────────

class TestCollectBuilding:
    """Module 1 (IFC Parser) is a stub — collector must fail gracefully."""

    def test_collect_building_raises_parser_unavailable(self):
        """collect_building() must raise ParserUnavailableError (Module 1 stub)."""
        collector = EvidenceCollector()
        with pytest.raises(ParserUnavailableError) as exc_info:
            collector.collect_building(_TEST_IFC)
        error = exc_info.value
        assert error.code == "PARSER_MODULE_UNAVAILABLE"
        assert error.module == "ifc_parser"

    def test_collect_building_error_as_dict(self):
        """ParserUnavailableError.as_dict() must return the correct structure."""
        collector = EvidenceCollector()
        with pytest.raises(ParserUnavailableError) as exc_info:
            collector.collect_building(_TEST_IFC)
        d = exc_info.value.as_dict()
        assert "error_code" in d
        assert "module" in d
        assert "detail" in d


# ─────────────────────────────────────────────────────────────────────────────
# 4. collect_classification() — Module 2 stub handling
# ─────────────────────────────────────────────────────────────────────────────

class TestCollectClassification:
    """Module 2 (Classification) is a stub — collector must fail gracefully."""

    def test_collect_classification_raises_unavailable(self):
        """collect_classification() must raise ClassificationUnavailableError."""
        collector = EvidenceCollector()
        building_ev = _make_building_evidence()
        with patch("app.report.evidence_collector._resolve_classification_service", side_effect=ClassificationUnavailableError(detail="Unavailable")):
            with pytest.raises(ClassificationUnavailableError) as exc_info:
                collector.collect_classification(building_ev)
            error = exc_info.value
            assert error.code == "CLASSIFICATION_MODULE_UNAVAILABLE"


# ─────────────────────────────────────────────────────────────────────────────
# 5. collect_compliance() — Compliance Engine stub handling
# ─────────────────────────────────────────────────────────────────────────────

class TestCollectCompliance:
    """Compliance Engine is a stub — collector must fail gracefully."""

    def test_collect_compliance_raises_unavailable(self):
        """collect_compliance() must raise ComplianceUnavailableError."""
        collector = EvidenceCollector()
        building_ev = _make_building_evidence()
        gis_ev = _make_gis_evidence()
        with patch("app.report.evidence_collector._resolve_compliance_service", side_effect=ComplianceUnavailableError(detail="Unavailable")):
            with pytest.raises(ComplianceUnavailableError) as exc_info:
                collector.collect_compliance(building_ev, gis_ev)
            error = exc_info.value
            assert error.code == "COMPLIANCE_MODULE_UNAVAILABLE"


# ─────────────────────────────────────────────────────────────────────────────
# 6. build_bundle() — propagates first upstream failure
# ─────────────────────────────────────────────────────────────────────────────

class TestBuildBundle:
    """build_bundle() must raise the correct domain exception on first failure."""

    def test_build_bundle_raises_parser_unavailable(self):
        """build_bundle() must raise ParserUnavailableError when Module 1 absent."""
        collector = EvidenceCollector()
        with patch("app.report.evidence_collector._resolve_parser_service", side_effect=ParserUnavailableError(detail="Unavailable")):
            with pytest.raises(ParserUnavailableError):
                collector.build_bundle(ifc_file=_TEST_IFC, lat=_JAYANAGAR_LAT, lon=_JAYANAGAR_LON)

    def test_build_bundle_gis_step_executes(self):
        """
        When building + classification are mocked, GIS collection must still run.
        Verifies that build_bundle() reaches the GIS step (Module 3 live).
        """
        collector = EvidenceCollector()
        building_ev = _make_building_evidence()
        classification_ev = _make_classification_evidence()

        with patch.object(collector, "collect_building", return_value=building_ev):
            with patch.object(
                collector, "collect_classification", return_value=classification_ev
            ):
                with patch("app.report.evidence_collector._resolve_compliance_service", side_effect=ComplianceUnavailableError(detail="Unavailable")):
                    with pytest.raises(ComplianceUnavailableError):
                        collector.build_bundle(
                            ifc_file=_TEST_IFC,
                            lat=_JAYANAGAR_LAT,
                            lon=_JAYANAGAR_LON,
                        )


    def test_build_bundle_full_mock_returns_bundle(self):
        """build_bundle() must return an EvidenceBundle when all collectors are mocked."""
        collector = EvidenceCollector()
        building_ev = _make_building_evidence()
        classification_ev = _make_classification_evidence()
        gis_ev = _make_gis_evidence()
        compliance_ev = _make_compliance_evidence()

        with patch.object(collector, "collect_building", return_value=building_ev):
            with patch.object(
                collector, "collect_classification", return_value=classification_ev
            ):
                with patch.object(collector, "collect_gis", return_value=gis_ev):
                    with patch.object(
                        collector, "collect_compliance", return_value=compliance_ev
                    ):
                        bundle = collector.build_bundle(
                            ifc_file=_TEST_IFC,
                            lat=_JAYANAGAR_LAT,
                            lon=_JAYANAGAR_LON,
                        )

        assert isinstance(bundle, EvidenceBundle)
        assert bundle.building.ifc_file == _TEST_IFC
        assert bundle.gis.ward == "Jayanagar"
        assert bundle.compliance.score == 92.0
        assert bundle.report_id  # UUID4 set
        assert bundle.software_version  # pulled from settings


# ─────────────────────────────────────────────────────────────────────────────
# 7. ReportService — structured error response
# ─────────────────────────────────────────────────────────────────────────────

class TestReportService:
    """ReportService.collect_evidence() must return structured error tuples."""

    def test_service_returns_error_tuple_on_parser_failure(self):
        """Service must return (ModuleErrorDetail, 503) when parser is a stub."""
        result = ReportService.collect_evidence(
            ifc_file=_TEST_IFC,
            lat=_JAYANAGAR_LAT,
            lon=_JAYANAGAR_LON,
        )
        assert isinstance(result, tuple), "Expected error tuple; got success bundle"
        error_detail, http_status = result
        assert isinstance(error_detail, ModuleErrorDetail)
        assert http_status == 503
        assert error_detail.error_code == "PARSER_MODULE_UNAVAILABLE"

    def test_service_returns_bundle_when_all_mocked(self):
        """Service must return EvidenceBundle when all collector steps succeed."""
        building_ev = _make_building_evidence()
        classification_ev = _make_classification_evidence()
        gis_ev = _make_gis_evidence()
        compliance_ev = _make_compliance_evidence()

        with patch(
            "app.report.service.EvidenceCollector.collect_building",
            return_value=building_ev,
        ):
            with patch(
                "app.report.service.EvidenceCollector.collect_classification",
                return_value=classification_ev,
            ):
                with patch(
                    "app.report.service.EvidenceCollector.collect_gis",
                    return_value=gis_ev,
                ):
                    with patch(
                        "app.report.service.EvidenceCollector.collect_compliance",
                        return_value=compliance_ev,
                    ):
                        result = ReportService.collect_evidence(
                            ifc_file=_TEST_IFC,
                            lat=_JAYANAGAR_LAT,
                            lon=_JAYANAGAR_LON,
                        )

        assert isinstance(result, EvidenceBundle)


# ─────────────────────────────────────────────────────────────────────────────
# 8 & 9. HTTP endpoint tests
# ─────────────────────────────────────────────────────────────────────────────

class TestReportEndpoint:
    """FastAPI GET /api/v1/report/context endpoint tests."""

    def test_endpoint_returns_503_when_parser_unavailable(self, client):
        """
        Without mocking, parser is a stub → HTTP 503 with ModuleErrorDetail body.
        """
        response = client.get(
            "/api/v1/report/context",
            params={
                "ifc_file": _TEST_IFC,
                "lat": _JAYANAGAR_LAT,
                "lon": _JAYANAGAR_LON,
            },
        )
        assert response.status_code == 503
        body = response.json()
        assert "error_code" in body
        assert "module" in body
        assert "detail" in body
        assert body["error_code"] == "PARSER_MODULE_UNAVAILABLE"

    def test_endpoint_returns_422_for_missing_params(self, client):
        """Endpoint must return 422 when required query params are absent."""
        response = client.get("/api/v1/report/context")
        assert response.status_code == 422

    def test_endpoint_returns_422_for_invalid_lat(self, client):
        """Endpoint must return 422 when lat is out of the valid range."""
        response = client.get(
            "/api/v1/report/context",
            params={"ifc_file": _TEST_IFC, "lat": 999.0, "lon": _JAYANAGAR_LON},
        )
        assert response.status_code == 422

    def test_endpoint_returns_200_with_full_mock(self, client):
        """
        Endpoint must return 200 with a valid EvidenceBundle body
        when all upstream modules are mocked.
        """
        building_ev = _make_building_evidence()
        classification_ev = _make_classification_evidence()
        gis_ev = _make_gis_evidence()
        compliance_ev = _make_compliance_evidence()

        with patch(
            "app.report.service.EvidenceCollector.collect_building",
            return_value=building_ev,
        ):
            with patch(
                "app.report.service.EvidenceCollector.collect_classification",
                return_value=classification_ev,
            ):
                with patch(
                    "app.report.service.EvidenceCollector.collect_gis",
                    return_value=gis_ev,
                ):
                    with patch(
                        "app.report.service.EvidenceCollector.collect_compliance",
                        return_value=compliance_ev,
                    ):
                        response = client.get(
                            "/api/v1/report/context",
                            params={
                                "ifc_file": _TEST_IFC,
                                "lat": _JAYANAGAR_LAT,
                                "lon": _JAYANAGAR_LON,
                            },
                        )

        assert response.status_code == 200
        body = response.json()

        # Verify top-level EvidenceBundle structure
        assert "report_id" in body
        assert "timestamp" in body
        assert "software_version" in body
        assert "building" in body
        assert "classification" in body
        assert "gis" in body
        assert "compliance" in body
        assert "metadata" in body

        # Spot-check nested values
        assert body["building"]["ifc_file"] == _TEST_IFC
        assert body["gis"]["authority"] == "BBMP"
        assert body["gis"]["ward"] == "Jayanagar"
        assert body["compliance"]["score"] == 92.0
        assert body["classification"]["predicted_type"] == "Residential"

    def test_endpoint_schema_completeness_with_mock(self, client):
        """
        All fields defined in EvidenceBundle must be present in the HTTP response.
        """
        building_ev = _make_building_evidence()
        classification_ev = _make_classification_evidence()
        gis_ev = _make_gis_evidence()
        compliance_ev = _make_compliance_evidence()

        with patch(
            "app.report.service.EvidenceCollector.collect_building",
            return_value=building_ev,
        ):
            with patch(
                "app.report.service.EvidenceCollector.collect_classification",
                return_value=classification_ev,
            ):
                with patch(
                    "app.report.service.EvidenceCollector.collect_gis",
                    return_value=gis_ev,
                ):
                    with patch(
                        "app.report.service.EvidenceCollector.collect_compliance",
                        return_value=compliance_ev,
                    ):
                        response = client.get(
                            "/api/v1/report/context",
                            params={
                                "ifc_file": _TEST_IFC,
                                "lat": _JAYANAGAR_LAT,
                                "lon": _JAYANAGAR_LON,
                            },
                        )

        body = response.json()

        # BuildingEvidence keys
        for key in ["building_id", "building_name", "ifc_file", "building_type",
                    "plot_area", "builtup_area", "height", "floors", "fsi",
                    "ground_coverage", "occupancy"]:
            assert key in body["building"], f"BuildingEvidence missing field: {key}"

        # GISEvidence keys
        for key in ["authority", "ward", "zone", "road_name", "road_width",
                    "land_use", "lake_distance", "lake_buffer", "airport_zone",
                    "flood_risk", "heritage_zone", "dataset_manifest"]:
            assert key in body["gis"], f"GISEvidence missing field: {key}"

        # ComplianceEvidence keys
        for key in ["rules_checked", "passed", "failed", "warnings",
                    "blocking", "score", "rule_results"]:
            assert key in body["compliance"], f"ComplianceEvidence missing field: {key}"

        # CollectionMetadata keys
        for key in ["collected_at", "total_collection_ms", "gis_engine_version"]:
            assert key in body["metadata"], f"CollectionMetadata missing field: {key}"


# ─────────────────────────────────────────────────────────────────────────────
# 10. Performance test
# ─────────────────────────────────────────────────────────────────────────────

class TestPerformance:
    """Evidence collection must meet timing requirements."""

    def test_gis_collection_within_200ms(self):
        """
        collect_gis() must complete within 200 ms on a warm GIS engine.
        (Consistent with the existing GIS module performance contract.)
        """
        collector = EvidenceCollector()
        t0 = perf_start()
        collector.collect_gis(_JAYANAGAR_LAT, _JAYANAGAR_LON)
        ms = elapsed_ms(t0)
        assert ms < 200.0, f"GIS collection took {ms:.2f} ms (must be < 200 ms)"

    def test_full_bundle_assembly_within_2000ms_when_mocked(self):
        """
        Full build_bundle() with all collectors mocked must complete within
        2 000 ms (all non-GIS work is in-process).
        """
        collector = EvidenceCollector()
        building_ev = _make_building_evidence()
        classification_ev = _make_classification_evidence()
        gis_ev = _make_gis_evidence()
        compliance_ev = _make_compliance_evidence()

        with patch.object(collector, "collect_building", return_value=building_ev):
            with patch.object(
                collector, "collect_classification", return_value=classification_ev
            ):
                with patch.object(collector, "collect_gis", return_value=gis_ev):
                    with patch.object(
                        collector, "collect_compliance", return_value=compliance_ev
                    ):
                        t0 = perf_start()
                        bundle = collector.build_bundle(
                            ifc_file=_TEST_IFC,
                            lat=_JAYANAGAR_LAT,
                            lon=_JAYANAGAR_LON,
                        )
                        ms = elapsed_ms(t0)

        assert ms < 2_000.0, f"Full bundle assembly took {ms:.2f} ms (must be < 2 000 ms)"
        assert bundle.metadata.total_collection_ms >= 0.0


# ─────────────────────────────────────────────────────────────────────────────
# 11. Utility function unit tests
# ─────────────────────────────────────────────────────────────────────────────

class TestUtils:
    """Pure utility function correctness."""

    def test_generate_report_id_is_uuid4(self):
        """generate_report_id() must return a valid UUID4 string."""
        rid = generate_report_id()
        parsed = uuid.UUID(rid, version=4)
        assert str(parsed) == rid

    def test_generate_report_id_unique(self):
        """Consecutive calls must return different IDs."""
        assert generate_report_id() != generate_report_id()

    def test_utc_now_is_timezone_aware(self):
        """utc_now() must return a timezone-aware datetime."""
        now = utc_now()
        assert now.tzinfo is not None
        assert now.tzinfo.utcoffset(now).total_seconds() == 0.0

    def test_elapsed_ms_positive(self):
        """elapsed_ms() must return a non-negative value."""
        t0 = perf_start()
        time.sleep(0.005)  # 5 ms sleep
        ms = elapsed_ms(t0)
        assert ms > 0.0

    def test_elapsed_ms_reasonable_upper_bound(self):
        """elapsed_ms() for a trivial operation must not exceed 500 ms."""
        t0 = perf_start()
        _ = 1 + 1
        ms = elapsed_ms(t0)
        assert ms < 500.0
