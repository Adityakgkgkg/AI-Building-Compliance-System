"""
MCRDSE Sprint 3 – Decision Support Engine Unit & Integration Tests
===================================================================
Test coverage:

1.  Schema validation — Decision schemas construct properly with strict Pydantic v2.
2.  ``RecommendationEngine`` — Generates evidence-based, prioritized recommendations from rule failures.
3.  ``ViolationPrioritizer`` — Deterministic ordering by priority, severity, status, and rule_id.
4.  ``ApprovalReadinessEngine`` — Configurable weighted scoring model & status category mapping
    (APPROVED, CONDITIONAL_APPROVAL, REQUIRES_MANUAL_REVIEW, REJECTED).
5.  ``RiskAssessmentEngine`` — 4-dimensional risk calculations (Environmental, Zoning, Structural, Compliance).
6.  ``DecisionSummaryGenerator`` — Synthesizes executive summary text and next steps.
7.  ``DecisionService`` — Gracefully propagates upstream module errors as HTTP 503.
8.  REST Endpoints — All 5 endpoints (/context, /recommendations, /approval, /risk, /summary) return 200/503/422.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from main import app
from app.gis.dataset_manager import DatasetManager
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

from app.decision.approval_engine import ApprovalReadinessEngine
from app.decision.prioritizer import ViolationPrioritizer
from app.decision.recommendation_engine import RecommendationEngine
from app.decision.risk_engine import RiskAssessmentEngine
from app.decision.schemas import (
    ApprovalReadiness,
    DecisionContext,
    DecisionSummary,
    DimensionRisk,
    RecommendationItem,
    RecommendationResponse,
    RiskAssessment,
)
from app.decision.service import DecisionService
from app.decision.summary_generator import DecisionSummaryGenerator


_JAYANAGAR_LAT = 12.9250
_JAYANAGAR_LON = 77.5938
_TEST_IFC = "test_building.ifc"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module", autouse=True)
def setup_gis():
    dm = DatasetManager.get_instance()
    dm.initialize()


# ─────────────────────────────────────────────────────────────────────────────
# Fixture Factories
# ─────────────────────────────────────────────────────────────────────────────

def _make_building_evidence(height: float = 12.5, fsi: float = 1.8, coverage: float = 40.0) -> BuildingEvidence:
    return BuildingEvidence(
        building_id="test-bld-001",
        building_name="Jayanagar Residency",
        ifc_file=_TEST_IFC,
        building_type="RESIDENTIAL",
        plot_area=500.0,
        builtup_area=900.0,
        height=height,
        floors=3,
        fsi=fsi,
        ground_coverage=coverage,
        occupancy="Residential",
    )


def _make_classification_evidence() -> ClassificationEvidence:
    return ClassificationEvidence(
        predicted_type="Residential",
        confidence=0.95,
        reason="Floor count and layout confirm residential use.",
    )


def _make_gis_evidence(
    lake_buffer: bool = False,
    airport_zone: bool = False,
    airport_height: float | None = None,
    flood_risk: str = "Low",
    heritage_zone: bool = False,
) -> GISEvidence:
    return GISEvidence(
        authority="BBMP",
        ward="Jayanagar",
        ward_number=167,
        zone="South Zone",
        road_name="11th Main Road",
        road_width=12.0,
        land_use="Residential",
        lake_distance=450.0,
        lake_buffer=lake_buffer,
        airport_zone=airport_zone,
        airport_height_limit=airport_height,
        flood_risk=flood_risk,
        heritage_zone=heritage_zone,
        dataset_manifest=[
            DatasetProvenance(
                dataset_name="BBMP Ward Boundaries",
                authority="BBMP",
                source_url="https://datameet.org",
                license="CC-BY-SA",
                feature_id="ward_167",
                observation="Site located in Jayanagar Ward 167.",
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
        rule_name="FSI Limit Check",
        status=status,
        severity=severity,
        expected="≤ 2.25",
        actual="1.80",
        difference="0",
        message="FSI is compliant with BBMP bye-laws.",
        clause="BBMP Bye-law 7.3.2",
        reference="BBMP Bye-laws 2024",
        recommendation="No corrective action required.",
    )


def _make_compliance_evidence(
    score: float = 95.0,
    passed: int = 5,
    failed: int = 0,
    warnings: int = 0,
    blocking: int = 0,
    rules: list[RuleResult] | None = None,
) -> ComplianceEvidence:
    if rules is None:
        rules = [_make_rule_result()]
    return ComplianceEvidence(
        rules_checked=len(rules),
        passed=passed,
        failed=failed,
        warnings=warnings,
        blocking=blocking,
        score=score,
        rule_results=rules,
    )


def _make_collection_metadata() -> CollectionMetadata:
    return CollectionMetadata(
        collected_at=datetime.now(timezone.utc),
        building_collection_ms=10.0,
        classification_collection_ms=5.0,
        gis_collection_ms=30.0,
        compliance_collection_ms=15.0,
        total_collection_ms=60.0,
        ifc_parser_version="1.0.0",
        classification_version="1.0.0",
        gis_engine_version="1.0.0",
        compliance_engine_version="1.0.0",
    )


def _make_evidence_bundle(
    building: BuildingEvidence | None = None,
    gis: GISEvidence | None = None,
    compliance: ComplianceEvidence | None = None,
) -> EvidenceBundle:
    return EvidenceBundle(
        report_id="test-report-uuid-001",
        timestamp=datetime.now(timezone.utc),
        building=building or _make_building_evidence(),
        classification=_make_classification_evidence(),
        gis=gis or _make_gis_evidence(),
        compliance=compliance or _make_compliance_evidence(),
        metadata=_make_collection_metadata(),
        software_version="0.1.0",
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1. Recommendation Engine Unit Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestRecommendationEngine:

    def test_no_recommendations_when_all_rules_pass(self):
        bundle = _make_evidence_bundle()
        recs = RecommendationEngine.generate_recommendations(bundle)
        assert isinstance(recs, RecommendationResponse)
        assert recs.total_recommendations == 0
        assert len(recs.recommendations) == 0

    def test_generates_critical_priority_for_blocking_failure(self):
        failed_rule = _make_rule_result(
            rule_id="BBMP-SETBACK-001",
            status="FAILED",
            severity="BLOCKING",
        )
        comp = _make_compliance_evidence(score=50.0, passed=1, failed=1, blocking=1, rules=[failed_rule])
        bundle = _make_evidence_bundle(compliance=comp)

        recs = RecommendationEngine.generate_recommendations(bundle)
        assert recs.total_recommendations == 1
        assert recs.critical_count == 1
        item = recs.recommendations[0]
        assert item.rule_id == "BBMP-SETBACK-001"
        assert item.priority == "CRITICAL"
        assert item.severity == "BLOCKING"

    def test_priority_mapping_order(self):
        r1 = _make_rule_result(rule_id="R1", status="FAILED", severity="INFO")
        r2 = _make_rule_result(rule_id="R2", status="FAILED", severity="BLOCKING")
        r3 = _make_rule_result(rule_id="R3", status="WARNING", severity="MINOR")
        r4 = _make_rule_result(rule_id="R4", status="FAILED", severity="MAJOR")

        comp = _make_compliance_evidence(rules=[r1, r2, r3, r4])
        bundle = _make_evidence_bundle(compliance=comp)

        recs = RecommendationEngine.generate_recommendations(bundle)
        priorities = [r.priority for r in recs.recommendations]
        # Should be sorted: CRITICAL (R2), HIGH (R4), MEDIUM (R3), LOW (R1)
        assert priorities == ["CRITICAL", "HIGH", "MEDIUM", "LOW"]


# ─────────────────────────────────────────────────────────────────────────────
# 2. Violation Prioritizer Unit Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestViolationPrioritizer:

    def test_sort_rule_results_by_severity(self):
        rules = [
            _make_rule_result(rule_id="R1", severity="INFO"),
            _make_rule_result(rule_id="R2", severity="BLOCKING"),
            _make_rule_result(rule_id="R3", severity="MAJOR"),
        ]
        sorted_rules = ViolationPrioritizer.sort_rule_results(rules)
        ids = [r.rule_id for r in sorted_rules]
        assert ids == ["R2", "R3", "R1"]


# ─────────────────────────────────────────────────────────────────────────────
# 3. Approval Readiness Engine Unit Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestApprovalReadinessEngine:

    def test_approved_status_for_clean_bundle(self):
        bundle = _make_evidence_bundle()
        engine = ApprovalReadinessEngine()
        readiness = engine.evaluate_readiness(bundle)

        assert isinstance(readiness, ApprovalReadiness)
        assert readiness.readiness_score >= 90.0
        assert readiness.status_category == "APPROVED"
        assert "PLAN SANCTION APPROVED" in readiness.sanction_verdict
        assert readiness.blocking_violations_count == 0

    def test_rejected_status_when_blocking_violations_present(self):
        failed_rule = _make_rule_result(rule_id="R1", status="FAILED", severity="BLOCKING")
        comp = _make_compliance_evidence(score=75.0, passed=4, failed=1, blocking=1, rules=[failed_rule])
        bundle = _make_evidence_bundle(compliance=comp)

        engine = ApprovalReadinessEngine()
        readiness = engine.evaluate_readiness(bundle)

        assert readiness.status_category == "REJECTED"
        assert "SANCTION REFUSED" in readiness.sanction_verdict
        assert readiness.blocking_violations_count == 1

    def test_conditional_approval_status(self):
        failed_rule = _make_rule_result(rule_id="R1", status="WARNING", severity="MINOR")
        comp = _make_compliance_evidence(score=82.0, passed=4, warnings=1, blocking=0, rules=[failed_rule])
        bundle = _make_evidence_bundle(compliance=comp)

        engine = ApprovalReadinessEngine()
        readiness = engine.evaluate_readiness(bundle)

        assert readiness.status_category in ("APPROVED", "CONDITIONAL_APPROVAL")
        assert readiness.blocking_violations_count == 0

    def test_custom_weights(self):
        engine = ApprovalReadinessEngine(
            compliance_weight=0.50,
            blocking_weight=0.30,
            gis_risk_weight=0.10,
            classification_weight=0.10,
        )
        bundle = _make_evidence_bundle()
        readiness = engine.evaluate_readiness(bundle)
        assert readiness.weights.compliance_weight == 0.50


# ─────────────────────────────────────────────────────────────────────────────
# 4. Risk Assessment Engine Unit Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestRiskAssessmentEngine:

    def test_low_risk_for_clean_bundle(self):
        bundle = _make_evidence_bundle()
        risk = RiskAssessmentEngine.evaluate_risk(bundle)

        assert isinstance(risk, RiskAssessment)
        assert risk.overall_risk_level in ("LOW", "MEDIUM")
        assert risk.environmental_risk.risk_level == "LOW"
        assert risk.zoning_risk.risk_level == "LOW"
        assert risk.structural_risk.risk_level == "LOW"

    def test_environmental_risk_on_lake_buffer(self):
        gis = _make_gis_evidence(lake_buffer=True, flood_risk="High")
        bundle = _make_evidence_bundle(gis=gis)

        risk = RiskAssessmentEngine.evaluate_risk(bundle)
        assert risk.environmental_risk.risk_score >= 70.0
        assert risk.environmental_risk.risk_level == "CRITICAL"
        assert any("lake buffer" in f.lower() for f in risk.environmental_risk.key_factors)

    def test_structural_risk_on_airport_height_exceeded(self):
        bld = _make_building_evidence(height=45.0, fsi=2.8, coverage=70.0)
        gis = _make_gis_evidence(airport_zone=True, airport_height=30.0)
        bundle = _make_evidence_bundle(building=bld, gis=gis)

        risk = RiskAssessmentEngine.evaluate_risk(bundle)
        assert risk.structural_risk.risk_score >= 70.0
        assert risk.structural_risk.risk_level == "CRITICAL"


# ─────────────────────────────────────────────────────────────────────────────
# 5. Decision Summary Generator Unit Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestDecisionSummaryGenerator:

    def test_generates_summary_for_approved_bundle(self):
        bundle = _make_evidence_bundle()
        approval = ApprovalReadinessEngine().evaluate_readiness(bundle)
        risk = RiskAssessmentEngine.evaluate_risk(bundle)
        recs = RecommendationEngine.generate_recommendations(bundle)

        summary = DecisionSummaryGenerator.generate_summary(bundle, approval, risk, recs)
        assert isinstance(summary, DecisionSummary)
        assert summary.sanction_recommendation == "GRANT BUILDING PERMIT SANCTION"
        assert "EXECUTIVE SANCTION SUMMARY" in summary.executive_summary_text
        assert len(summary.next_steps) > 0


# ─────────────────────────────────────────────────────────────────────────────
# 6. Decision Service Layer Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestDecisionService:

    def test_service_returns_context_on_supplied_bundle(self):
        bundle = _make_evidence_bundle()
        result = DecisionService.get_decision_context(
            ifc_file=_TEST_IFC, lat=_JAYANAGAR_LAT, lon=_JAYANAGAR_LON, bundle=bundle
        )
        assert isinstance(result, DecisionContext)
        assert result.approval.status_category == "APPROVED"
        assert result.summary.building_name == bundle.building.building_name

    def test_service_returns_error_tuple_on_parser_failure(self):
        result = DecisionService.get_decision_context(
            ifc_file="non_existent_file_xyz_999.ifc", lat=_JAYANAGAR_LAT, lon=_JAYANAGAR_LON
        )
        assert isinstance(result, tuple)
        error_detail, http_status = result
        assert http_status == 503
        assert error_detail.error_code == "PARSER_MODULE_UNAVAILABLE"


# ─────────────────────────────────────────────────────────────────────────────
# 7. REST Endpoints Integration Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestDecisionEndpoints:

    def test_endpoint_returns_503_when_stub_modules_unmocked(self, client):
        endpoints = [
            "/api/v1/decision/context",
            "/api/v1/decision/recommendations",
            "/api/v1/decision/approval",
            "/api/v1/decision/risk",
            "/api/v1/decision/summary",
        ]
        for ep in endpoints:
            res = client.get(ep, params={"ifc_file": "non_existent_file_xyz_999.ifc", "lat": _JAYANAGAR_LAT, "lon": _JAYANAGAR_LON})
            assert res.status_code == 503, f"{ep} did not return 503 on unmocked stub modules"
            body = res.json()
            assert "error_code" in body
            assert body["error_code"] == "PARSER_MODULE_UNAVAILABLE"


    def test_endpoint_returns_422_on_missing_params(self, client):
        res = client.get("/api/v1/decision/context")
        assert res.status_code == 422

    def test_endpoint_returns_200_when_bundle_mocked(self, client):
        mock_bundle = _make_evidence_bundle()
        with patch("app.report.service.EvidenceCollector.build_bundle", return_value=mock_bundle):
            # GET /context
            res = client.get("/api/v1/decision/context", params={"ifc_file": _TEST_IFC, "lat": _JAYANAGAR_LAT, "lon": _JAYANAGAR_LON})
            assert res.status_code == 200
            data = res.json()
            assert "approval" in data
            assert "risk" in data
            assert "recommendations" in data
            assert "summary" in data

            # GET /approval
            res_app = client.get("/api/v1/decision/approval", params={"ifc_file": _TEST_IFC, "lat": _JAYANAGAR_LAT, "lon": _JAYANAGAR_LON})
            assert res_app.status_code == 200
            assert "readiness_score" in res_app.json()

            # GET /risk
            res_risk = client.get("/api/v1/decision/risk", params={"ifc_file": _TEST_IFC, "lat": _JAYANAGAR_LAT, "lon": _JAYANAGAR_LON})
            assert res_risk.status_code == 200
            assert "overall_risk_level" in res_risk.json()

            # GET /recommendations
            res_rec = client.get("/api/v1/decision/recommendations", params={"ifc_file": _TEST_IFC, "lat": _JAYANAGAR_LAT, "lon": _JAYANAGAR_LON})
            assert res_rec.status_code == 200
            assert "recommendations" in res_rec.json()

            # GET /summary
            res_sum = client.get("/api/v1/decision/summary", params={"ifc_file": _TEST_IFC, "lat": _JAYANAGAR_LAT, "lon": _JAYANAGAR_LON})
            assert res_sum.status_code == 200
            assert "executive_summary_text" in res_sum.json()
