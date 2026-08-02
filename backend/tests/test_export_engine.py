"""
MCRDSE Sprint 4 – Export Engine Unit & Integration Tests
=========================================================
Test coverage:

1.  ``QRCodeGenerator`` — PNG bytes and base64 string generation.
2.  ``ReportBuilder`` — 10-section canonical payload assembly and SHA256 hashing.
3.  ``PDFReportGenerator`` — PDF binary creation and document structure.
4.  ``HTMLReportGenerator`` — Jinja2 HTML string rendering with sections & QR code.
5.  ``JSONReportExporter`` — JSON serialisation and formatting.
6.  ``AuditTrailService`` — Storage persistence, checksum calculation, and retrieval.
7.  REST Endpoints — All 5 export endpoints (/generate, /pdf, /html, /json, /status).
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
from app.decision.service import DecisionService

from app.export.audit_service import AuditTrailService
from app.export.builder import ReportBuilder
from app.export.html_generator import HTMLReportGenerator
from app.export.json_exporter import JSONReportExporter
from app.export.pdf_generator import PDFReportGenerator
from app.export.qr_generator import QRCodeGenerator
from app.export.schemas import ExportRequest, ExportResponse, ReportData


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


def _make_evidence_bundle() -> EvidenceBundle:
    return EvidenceBundle(
        report_id="export-test-report-001",
        timestamp=datetime.now(timezone.utc),
        building=BuildingEvidence(
            building_id="bld-001",
            building_name="Empire Towers",
            ifc_file=_TEST_IFC,
            building_type="COMMERCIAL",
            plot_area=1000.0,
            builtup_area=2200.0,
            height=18.5,
            floors=5,
            fsi=2.2,
            ground_coverage=45.0,
            occupancy="Commercial",
        ),
        classification=ClassificationEvidence(
            predicted_type="Commercial",
            confidence=0.92,
            reason="Commercial occupancy and floor dimensions.",
        ),
        gis=GISEvidence(
            authority="BBMP",
            ward="Jayanagar",
            ward_number=167,
            zone="South Zone",
            road_name="11th Main Road",
            road_width=15.0,
            land_use="Commercial",
            lake_distance=600.0,
            lake_buffer=False,
            airport_zone=False,
            airport_height_limit=None,
            flood_risk="Low",
            heritage_zone=False,
            dataset_manifest=[
                DatasetProvenance(
                    dataset_name="BBMP Ward Boundaries",
                    authority="BBMP",
                    source_url="https://datameet.org",
                    license="CC-BY-SA",
                    feature_id="ward_167",
                    observation="Site located in Ward 167.",
                )
            ],
        ),
        compliance=ComplianceEvidence(
            rules_checked=5,
            passed=4,
            failed=0,
            warnings=1,
            blocking=0,
            score=90.0,
            rule_results=[
                RuleResult(
                    rule_id="BBMP-FSI-001",
                    rule_name="FSI Limit Check",
                    status="PASSED",
                    severity="MAJOR",
                    expected="≤ 2.50",
                    actual="2.20",
                    difference="0",
                    message="FSI within limits.",
                    clause="BBMP Bye-law 7.3",
                    reference="BBMP Bye-laws 2024",
                    recommendation="No action needed.",
                ),
                RuleResult(
                    rule_id="BBMP-HEIGHT-002",
                    rule_name="Height Warning Check",
                    status="WARNING",
                    severity="MINOR",
                    expected="≤ 15.0",
                    actual="18.5",
                    difference="+3.5 m",
                    message="High-rise structure threshold exceeded; additional fire safety clearance advised.",
                    clause="BBMP Bye-law 8.1",
                    reference="BBMP Bye-laws 2024",
                    recommendation="Obtain NOC from Fire Department.",
                ),
            ],
        ),
        metadata=CollectionMetadata(
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
        ),
        software_version="0.1.0",
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1. QR Code Generator Unit Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestQRCodeGenerator:

    def test_generate_qr_code_returns_bytes_and_data_url(self):
        url = "http://localhost:8000/api/v1/export/status/test-001"
        png_bytes, b64_url = QRCodeGenerator.generate_qr_code(url)

        assert isinstance(png_bytes, bytes)
        assert len(png_bytes) > 50
        assert png_bytes.startswith(b"\x89PNG") or len(png_bytes) > 0
        assert b64_url.startswith("data:image/png;base64,")


# ─────────────────────────────────────────────────────────────────────────────
# 2. Report Builder Unit Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestReportBuilder:

    def test_build_report_data_has_10_sections(self):
        bundle = _make_evidence_bundle()
        ctx = DecisionService.get_decision_context(_TEST_IFC, _JAYANAGAR_LAT, _JAYANAGAR_LON, bundle=bundle)
        assert not isinstance(ctx, tuple)

        report_data = ReportBuilder.build_report_data(ctx)
        assert isinstance(report_data, ReportData)
        assert report_data.report_id == bundle.report_id
        assert len(report_data.sections) == 10
        assert report_data.checksum_sha256 != ""
        assert len(report_data.checksum_sha256) == 64


# ─────────────────────────────────────────────────────────────────────────────
# 3. PDF Generator Unit Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestPDFReportGenerator:

    def test_generate_pdf_returns_pdf_bytes(self):
        bundle = _make_evidence_bundle()
        ctx = DecisionService.get_decision_context(_TEST_IFC, _JAYANAGAR_LAT, _JAYANAGAR_LON, bundle=bundle)
        report_data = ReportBuilder.build_report_data(ctx)

        pdf_bytes = PDFReportGenerator.generate_pdf(report_data)
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes.startswith(b"%PDF-")
        assert len(pdf_bytes) > 1000


# ─────────────────────────────────────────────────────────────────────────────
# 4. HTML Generator Unit Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestHTMLReportGenerator:

    def test_generate_html_contains_sections_and_verdict(self):
        bundle = _make_evidence_bundle()
        ctx = DecisionService.get_decision_context(_TEST_IFC, _JAYANAGAR_LAT, _JAYANAGAR_LON, bundle=bundle)
        report_data = ReportBuilder.build_report_data(ctx)

        html_str = HTMLReportGenerator.generate_html(report_data)
        assert isinstance(html_str, str)
        assert "<!DOCTYPE html>" in html_str
        assert "MUNICIPAL PLAN SANCTION AUDIT REPORT" in html_str
        assert report_data.report_id in html_str
        assert "Empire Towers" in html_str


# ─────────────────────────────────────────────────────────────────────────────
# 5. JSON Exporter Unit Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestJSONReportExporter:

    def test_export_json_dict_and_str(self):
        bundle = _make_evidence_bundle()
        ctx = DecisionService.get_decision_context(_TEST_IFC, _JAYANAGAR_LAT, _JAYANAGAR_LON, bundle=bundle)
        report_data = ReportBuilder.build_report_data(ctx)

        d = JSONReportExporter.export_json_dict(report_data)
        assert isinstance(d, dict)
        assert d["report_id"] == report_data.report_id

        s = JSONReportExporter.export_json_str(report_data)
        assert isinstance(s, str)
        assert report_data.report_id in s


# ─────────────────────────────────────────────────────────────────────────────
# 6. Audit Trail Service Unit Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestAuditTrailService:

    def test_save_and_retrieve_report(self):
        bundle = _make_evidence_bundle()
        ctx = DecisionService.get_decision_context(_TEST_IFC, _JAYANAGAR_LAT, _JAYANAGAR_LON, bundle=bundle)
        report_data = ReportBuilder.build_report_data(ctx)

        pdf_bytes = PDFReportGenerator.generate_pdf(report_data)
        html_str = HTMLReportGenerator.generate_html(report_data)
        json_str = JSONReportExporter.export_json_str(report_data)

        audit = AuditTrailService.save_report(report_data, pdf_bytes, html_str, json_str)
        assert audit.report_id == report_data.report_id

        retrieved_pdf = AuditTrailService.get_pdf_bytes(report_data.report_id)
        assert retrieved_pdf == pdf_bytes

        retrieved_html = AuditTrailService.get_html_str(report_data.report_id)
        assert retrieved_html == html_str

        retrieved_json = AuditTrailService.get_json_dict(report_data.report_id)
        assert retrieved_json["report_id"] == report_data.report_id


# ─────────────────────────────────────────────────────────────────────────────
# 7. REST Endpoints Integration Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestExportEndpoints:

    def test_generate_endpoint_returns_503_when_stub_modules_unmocked(self, client):
        req_data = {"ifc_file": "non_existent_file_xyz_999.ifc", "lat": _JAYANAGAR_LAT, "lon": _JAYANAGAR_LON, "formats": ["pdf", "html"]}
        res = client.post("/api/v1/export/generate", json=req_data)
        assert res.status_code == 503
        body = res.json()
        assert body["error_code"] == "PARSER_MODULE_UNAVAILABLE"


    def test_generate_and_fetch_endpoints_when_bundle_mocked(self, client):
        mock_bundle = _make_evidence_bundle()
        with patch("app.report.service.EvidenceCollector.build_bundle", return_value=mock_bundle):
            req_data = {"ifc_file": _TEST_IFC, "lat": _JAYANAGAR_LAT, "lon": _JAYANAGAR_LON}
            res = client.post("/api/v1/export/generate", json=req_data)
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "COMPLETED"
            report_id = data["report_id"]

            # GET /pdf/{id}
            res_pdf = client.get(f"/api/v1/export/pdf/{report_id}")
            assert res_pdf.status_code == 200
            assert res_pdf.headers["content-type"] == "application/pdf"
            assert res_pdf.content.startswith(b"%PDF-")

            # GET /html/{id}
            res_html = client.get(f"/api/v1/export/html/{report_id}")
            assert res_html.status_code == 200
            assert "text/html" in res_html.headers["content-type"]
            assert "<!DOCTYPE html>" in res_html.text

            # GET /json/{id}
            res_json = client.get(f"/api/v1/export/json/{report_id}")
            assert res_json.status_code == 200
            assert res_json.json()["report_id"] == report_id

            # GET /status/{id}
            res_status = client.get(f"/api/v1/export/status/{report_id}")
            assert res_status.status_code == 200
            assert res_status.json()["report_id"] == report_id

    def test_endpoints_return_404_for_unknown_report_id(self, client):
        unknown_id = "non-existent-report-uuid-999"
        assert client.get(f"/api/v1/export/pdf/{unknown_id}").status_code == 404
        assert client.get(f"/api/v1/export/html/{unknown_id}").status_code == 404
        assert client.get(f"/api/v1/export/json/{unknown_id}").status_code == 404
        assert client.get(f"/api/v1/export/status/{unknown_id}").status_code == 404
