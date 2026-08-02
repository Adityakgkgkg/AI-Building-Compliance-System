"""
MCRDSE Module 1 – IFC Parser Engine Unit & Integration Tests
============================================================
Test coverage:

1.  Synthetic IFC file generation (IFC2X3 and IFC4) via IfcOpenShell.
2.  ``IFCParserEngine.open_model()`` — Valid opening, corrupt file rejection, unsupported schema handling.
3.  ``IFCValidator.validate_model()`` — Missing IfcBuilding validation.
4.  Sub-engine extraction — Metadata, 3D Geometry, Storeys, Spaces, Element Counts, Statistics.
5.  ``IFCParserService.parse()`` — Canonical ``ParsedBuildingResult`` interface matching EvidenceCollector.
6.  Integration Test — ``EvidenceCollector.collect_building()`` seamless execution.
7.  REST Endpoints — GET /health, POST /upload, GET /metadata, GET /statistics.
8.  Performance Benchmarks — Open time < 500 ms, Parse time < 3 000 ms.
"""

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

import ifcopenshell
import pytest
from fastapi.testclient import TestClient

from main import app
from app.parser.exceptions import (
    BuildingNotFoundError,
    IFCFileNotFoundError,
    InvalidIFCFileError,
    UnsupportedIFCSchemaError,
)
from app.parser.parser_engine import IFCParserEngine
from app.parser.schemas import (
    IFCElementCount,
    IFCGeometry,
    IFCHealthStatus,
    IFCMetadata,
    IFCParseSummary,
    IFCSpace,
    IFCStatistics,
    IFCStorey,
    ParsedBuildingResult,
)
from app.parser.service import IFCParserService
from app.parser.validator import IFCValidator
from app.report.evidence_collector import EvidenceCollector
from app.report.schemas import BuildingEvidence


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# ─────────────────────────────────────────────────────────────────────────────
# Synthetic IFC File Generators
# ─────────────────────────────────────────────────────────────────────────────

def _create_synthetic_ifc(schema: str = "IFC4", num_storeys: int = 3) -> Path:
    """
    Create a minimal valid IFC model using IfcOpenShell and save to a temp file.
    """
    f = ifcopenshell.file(schema=schema)

    # Header / Owner
    person = f.createIfcPerson(GivenName="BIM", FamilyName="Architect")
    org = f.createIfcOrganization(Name="Municipal Design Bureau")
    person_org = f.createIfcPersonAndOrganization(ThePerson=person, TheOrganization=org)
    app_entity = f.createIfcApplication(
        ApplicationDeveloper=org,
        Version="2026.1",
        ApplicationFullName="Municipal IFC Authoring Suite",
        ApplicationIdentifier="MUNICIPAL_BIM",
    )
    owner_hist = f.createIfcOwnerHistory(
        OwningUser=person_org,
        OwningApplication=app_entity,
        ChangeAction="ADDED",
        CreationDate=1700000000,
    )

    # Context & Units
    unit_assignment = f.createIfcUnitAssignment(
        Units=[
            f.createIfcSIUnit(UnitType="LENGTHUNIT", Name="METRE"),
            f.createIfcSIUnit(UnitType="AREAUNIT", Name="SQUARE_METRE"),
        ]
    )
    project = f.createIfcProject(
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner_hist,
        Name="Jayanagar Municipal Commercial Tower",
        UnitsInContext=unit_assignment,
    )

    site = f.createIfcSite(
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner_hist,
        Name="Jayanagar Plot 405",
    )

    building = f.createIfcBuilding(
        GlobalId="BLD-IFC-TEST-001",
        OwnerHistory=owner_hist,
        Name="Jayanagar Residency",
        ObjectType="RESIDENTIAL",
    )

    # Hierarchical Aggregation
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
        RelatedObjects=[building],
    )

    # Add Storeys
    storey_objs = []
    for i in range(num_storeys):
        st = f.createIfcBuildingStorey(
            GlobalId=f"STOREY-GUID-{i+1:03d}",
            OwnerHistory=owner_hist,
            Name=f"Level {i+1}",
            Elevation=float(i * 3.5),
        )
        storey_objs.append(st)

        # Add spaces
        sp = f.createIfcSpace(
            GlobalId=f"SPACE-GUID-{i+1:03d}",
            OwnerHistory=owner_hist,
            Name=f"Room {i+1}01",
            ObjectType="Living Room",
        )
        f.createIfcRelContainedInSpatialStructure(
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=owner_hist,
            RelatingStructure=st,
            RelatedElements=[sp],
        )

        # Add Wall
        wall = f.createIfcWall(
            GlobalId=f"WALL-GUID-{i+1:03d}",
            OwnerHistory=owner_hist,
            Name=f"Exterior Wall {i+1}",
        )
        f.createIfcRelContainedInSpatialStructure(
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=owner_hist,
            RelatingStructure=st,
            RelatedElements=[wall],
        )

    f.createIfcRelAggregates(
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner_hist,
        RelatingObject=building,
        RelatedObjects=storey_objs,
    )

    # Save to temp file
    tmp = tempfile.NamedTemporaryFile(suffix=".ifc", delete=False)
    f.write(tmp.name)
    tmp.close()
    return Path(tmp.name)


@pytest.fixture(scope="module")
def ifc4_file():
    p = _create_synthetic_ifc(schema="IFC4", num_storeys=3)
    yield p
    if p.exists():
        p.unlink()


@pytest.fixture(scope="module")
def ifc2x3_file():
    p = _create_synthetic_ifc(schema="IFC2X3", num_storeys=2)
    yield p
    if p.exists():
        p.unlink()


# ─────────────────────────────────────────────────────────────────────────────
# 1. IFCParserEngine Core & Error Handling Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestIFCParserEngine:

    def test_open_valid_ifc4_model(self, ifc4_file):
        model = IFCParserEngine.open_model(ifc4_file)
        assert model is not None
        assert len(model.by_type("IfcBuilding")) > 0

    def test_open_valid_ifc2x3_model(self, ifc2x3_file):
        model = IFCParserEngine.open_model(ifc2x3_file)
        assert model is not None
        assert len(model.by_type("IfcBuilding")) > 0

    def test_raises_non_existent_file(self):
        with pytest.raises(IFCFileNotFoundError):
            IFCParserService.parse("non_existent_file_999.ifc")

    def test_raises_invalid_corrupt_file(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".ifc", delete=False)
        tmp.write(b"NOT A VALID IFC FILE CONTENT 123456789")
        tmp.close()
        tmp_path = Path(tmp.name)

        try:
            with pytest.raises(InvalidIFCFileError):
                IFCParserEngine.open_model(tmp_path)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_validator_raises_building_not_found(self):
        f = ifcopenshell.file(schema="IFC4")
        tmp = tempfile.NamedTemporaryFile(suffix=".ifc", delete=False)
        f.write(tmp.name)
        tmp.close()
        p = Path(tmp.name)

        try:
            model = IFCParserEngine.open_model(p)
            with pytest.raises(BuildingNotFoundError):
                IFCValidator.validate_model(model)
        finally:
            if p.exists():
                p.unlink()


# ─────────────────────────────────────────────────────────────────────────────
# 2. Engine Extraction Subcomponents
# ─────────────────────────────────────────────────────────────────────────────

class TestSubEngines:

    def test_metadata_extraction(self, ifc4_file):
        meta = IFCParserService.extract_metadata(ifc4_file)
        assert isinstance(meta, IFCMetadata)
        assert meta.global_id == "BLD-IFC-TEST-001"
        assert meta.building_name == "Jayanagar Residency"
        assert meta.project_name == "Jayanagar Municipal Commercial Tower"
        assert meta.building_type == "RESIDENTIAL"
        assert meta.schema_version == "IFC4"

    def test_geometry_extraction(self, ifc4_file):
        geom = IFCParserService.extract_geometry(ifc4_file)
        assert isinstance(geom, IFCGeometry)
        assert geom.building_height > 0.0
        assert geom.building_length > 0.0
        assert geom.building_width > 0.0
        assert geom.bounding_box.centroid_z >= 0.0

    def test_storey_extraction(self, ifc4_file):
        storeys = IFCParserService.extract_storeys(ifc4_file)
        assert isinstance(storeys, list)
        assert len(storeys) == 3
        assert all(isinstance(st, IFCStorey) for st in storeys)
        assert storeys[0].name == "Level 1"
        assert storeys[0].global_id == "STOREY-GUID-001"

    def test_space_extraction(self, ifc4_file):
        spaces = IFCParserService.extract_spaces(ifc4_file)
        assert isinstance(spaces, list)
        assert len(spaces) == 3
        assert all(isinstance(sp, IFCSpace) for sp in spaces)
        assert spaces[0].name == "Room 101"
        assert spaces[0].global_id == "SPACE-GUID-001"

    def test_element_counts(self, ifc4_file):
        elements = IFCParserService.extract_elements(ifc4_file)
        assert isinstance(elements, IFCElementCount)
        assert elements.walls == 3
        assert elements.spaces == 3
        assert elements.storeys == 3
        assert elements.total >= 9

    def test_statistics_aggregation(self, ifc4_file):
        stats = IFCStatisticsService = IFCParserService.extract_statistics(ifc4_file)
        assert isinstance(stats, IFCStatistics)
        assert stats.floors == 3
        assert stats.builtup_area > 0.0
        assert stats.plot_area > 0.0
        assert stats.fsi > 0.0


# ─────────────────────────────────────────────────────────────────────────────
# 3. Canonical Service & Downstream EvidenceCollector Integration
# ─────────────────────────────────────────────────────────────────────────────

class TestServiceAndDownstreamIntegration:

    def test_parse_returns_parsed_building_result(self, ifc4_file):
        result = IFCParserService.parse(ifc4_file)
        assert isinstance(result, ParsedBuildingResult)
        assert result.building_id == "BLD-IFC-TEST-001"
        assert result.building_name == "Jayanagar Residency"
        assert result.building_type == "RESIDENTIAL"
        assert result.height > 0.0
        assert result.floors == 3
        assert result.builtup_area > 0.0
        assert result.plot_area > 0.0
        assert result.fsi > 0.0
        assert 0.0 <= result.ground_coverage <= 100.0

    def test_evidence_collector_integration(self, ifc4_file):
        """
        MANDATORY VERIFICATION: EvidenceCollector.collect_building() must call
        IFCParserService.parse() seamlessly and return a canonical BuildingEvidence object!
        """
        collector = EvidenceCollector()
        building_ev = collector.collect_building(str(ifc4_file))

        assert isinstance(building_ev, BuildingEvidence)
        assert building_ev.building_id == "BLD-IFC-TEST-001"
        assert building_ev.building_name == "Jayanagar Residency"
        assert building_ev.building_type == "RESIDENTIAL"
        assert building_ev.floors == 3
        assert building_ev.height > 0.0
        assert building_ev.fsi > 0.0


# ─────────────────────────────────────────────────────────────────────────────
# 4. REST Endpoints Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestParserEndpoints:

    def test_health_endpoint(self, client):
        res = client.get("/api/v1/parser/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert "ifcopenshell_version" in data
        assert "IFC4" in data["supported_schemas"]

    def test_upload_endpoint(self, client, ifc4_file):
        with open(ifc4_file, "rb") as f:
            res = client.post("/api/v1/parser/upload", files={"file": ("test_upload.ifc", f, "application/octet-stream")})
        assert res.status_code == 200
        data = res.json()
        assert "building_evidence" in data
        assert data["building_evidence"]["building_name"] == "Jayanagar Residency"
        assert "metadata" in data
        assert "geometry" in data
        assert "statistics" in data

    def test_metadata_endpoint(self, client, ifc4_file):
        res = client.get("/api/v1/parser/metadata", params={"ifc_file": str(ifc4_file)})
        assert res.status_code == 200
        data = res.json()
        assert data["building_name"] == "Jayanagar Residency"

    def test_statistics_endpoint(self, client, ifc4_file):
        res = client.get("/api/v1/parser/statistics", params={"ifc_file": str(ifc4_file)})
        assert res.status_code == 200
        data = res.json()
        assert data["floors"] == 3


# ─────────────────────────────────────────────────────────────────────────────
# 5. Performance Benchmarks
# ─────────────────────────────────────────────────────────────────────────────

class TestPerformance:

    def test_open_model_within_500ms(self, ifc4_file):
        t0 = IFCParserService.perf_start if hasattr(IFCParserService, "perf_start") else pytest.importorskip("time").perf_counter
        import time
        start = time.perf_counter()
        _ = IFCParserEngine.open_model(ifc4_file)
        ms = (time.perf_counter() - start) * 1000.0
        assert ms < 500.0, f"open_model took {ms:.2f} ms (> 500 ms target)"

    def test_full_parse_within_3000ms(self, ifc4_file):
        import time
        start = time.perf_counter()
        _ = IFCParserService.parse_full(ifc4_file)
        ms = (time.perf_counter() - start) * 1000.0
        assert ms < 3000.0, f"parse_full took {ms:.2f} ms (> 3000 ms target)"
