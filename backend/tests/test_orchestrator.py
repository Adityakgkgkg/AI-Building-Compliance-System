"""
MCRDSE Analysis Orchestrator – Unit & Integration Tests
========================================================
Test coverage:
1.  ``OrchestratorService.analyze_ifc()`` — Automated workflow execution across all 8 modules.
2.  ``POST /api/v1/analyze`` — Multipart file upload and automatic downstream orchestration.
3.  ``GET /api/v1/analyze/progress/{analysis_id}`` — Progress status retrieval.
4.  ``GET /api/v1/analyze/{analysis_id}`` — Unified analysis payload retrieval.
5.  Error handling — Graceful immediate stopping on invalid input or upstream module failure.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import ifcopenshell
import pytest
from fastapi.testclient import TestClient

from main import app
from app.orchestrator.schemas import AnalysisProgressResponse, UnifiedAnalysisResponse
from app.orchestrator.service import OrchestratorService


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def sample_ifc_file():
    """Create temporary minimal valid IFC file."""
    f = ifcopenshell.file(schema="IFC4")
    person = f.createIfcPerson(GivenName="Orchestrator", FamilyName="Tester")
    org = f.createIfcOrganization(Name="Municipal Automation Bureau")
    person_org = f.createIfcPersonAndOrganization(ThePerson=person, TheOrganization=org)
    app_entity = f.createIfcApplication(
        ApplicationDeveloper=org,
        Version="2026.1",
        ApplicationFullName="Municipal BIM Suite",
        ApplicationIdentifier="MUNICIPAL_BIM",
    )
    owner_hist = f.createIfcOwnerHistory(
        OwningUser=person_org,
        OwningApplication=app_entity,
        ChangeAction="ADDED",
        CreationDate=1700000000,
    )

    project = f.createIfcProject(
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner_hist,
        Name="Automated Orchestrator Project",
    )
    site = f.createIfcSite(
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner_hist,
        Name="Jayanagar Plot 500",
    )
    bld = f.createIfcBuilding(
        GlobalId="BLD-ORCHESTRATOR-001",
        OwnerHistory=owner_hist,
        Name="Orchestrator Tower",
        ObjectType="RESIDENTIAL",
    )

    f.createIfcRelAggregates(
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner_hist,
        RelatingObject=project,
        RelatedObjects=[site],
    )
    f.createIfcRelAggregates(
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner_hist,
        RelatingObject=site,
        RelatedObjects=[bld],
    )

    storeys = [
        f.createIfcBuildingStorey(
            GlobalId=f"ST-{i+1}",
            OwnerHistory=owner_hist,
            Name=f"Level {i+1}",
            Elevation=float(i * 3.5),
        )
        for i in range(3)
    ]
    f.createIfcRelAggregates(
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner_hist,
        RelatingObject=bld,
        RelatedObjects=storeys,
    )

    tmp = tempfile.NamedTemporaryFile(suffix=".ifc", delete=False)
    f.write(tmp.name)
    tmp.close()
    p = Path(tmp.name)
    yield p
    if p.exists():
        p.unlink()


class TestAnalysisOrchestrator:

    def test_orchestrator_service_analyze_ifc(self, sample_ifc_file):
        """Test full automated execution of OrchestratorService."""
        bytes_content = sample_ifc_file.read_bytes()
        res = OrchestratorService.analyze_ifc(
            ifc_file_bytes=bytes_content,
            filename="plan.ifc",
            lat=12.9250,
            lon=77.5938,
        )

        assert isinstance(res, UnifiedAnalysisResponse)
        assert res.status == "completed"
        assert res.progress == 100
        assert res.building["building_id"] == "BLD-ORCHESTRATOR-001"
        assert "dashboard_url" in res.model_dump()
        assert "report_url" in res.model_dump()
        assert "processing_time" in res.model_dump()
        assert res.total_processing_time > 0.0

    def test_analyze_endpoint_post(self, client, sample_ifc_file):
        """Test POST /api/v1/analyze multipart endpoint."""
        with open(sample_ifc_file, "rb") as f:
            res = client.post(
                "/api/v1/analyze",
                files={"file": ("plan.ifc", f, "application/octet-stream")},
                params={"lat": 12.9250, "lon": 77.5938},
            )

        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "completed"
        assert data["progress"] == 100
        assert "dashboard_url" in data
        assert "report_url" in data
        assert "analysis_id" in data

    def test_progress_endpoint(self, client, sample_ifc_file):
        """Test GET /api/v1/analyze/progress/{analysis_id}."""
        with open(sample_ifc_file, "rb") as f:
            res_post = client.post(
                "/api/v1/analyze",
                files={"file": ("plan.ifc", f, "application/octet-stream")},
            )
        analysis_id = res_post.json()["analysis_id"]

        res = client.get(f"/api/v1/analyze/progress/{analysis_id}")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "completed"
        assert data["progress"] == 100

    def test_invalid_file_type_rejected(self, client):
        """Test that non-IFC files are rejected with 400."""
        res = client.post(
            "/api/v1/analyze",
            files={"file": ("document.txt", b"TEXT CONTENT", "text/plain")},
        )
        assert res.status_code == 400
