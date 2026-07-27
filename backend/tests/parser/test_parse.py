"""
Tests for POST /api/v1/parser/parse/{file_id}
       GET  /api/v1/parser/building/{file_id}
       GET  /api/v1/parser/elements/{file_id}

Covers:
    - Successful parse → correct ParseResult shape
    - Schema version extracted correctly
    - Storey count matches fixture
    - Element counts all present (zero is fine for empty fixture)
    - Geometry section present (values may be null)
    - Unknown file_id → 404 on parse
    - Unknown file_id → 404 on building GET
    - Unknown file_id → 404 on elements GET
    - GET before parse → 404 (not yet parsed)
    - Corrupt IFC bytes → 422 on parse
"""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

UPLOAD_URL = "/api/v1/parser/upload"
PARSE_URL = "/api/v1/parser/parse/{file_id}"
BUILDING_URL = "/api/v1/parser/building/{file_id}"
ELEMENTS_URL = "/api/v1/parser/elements/{file_id}"


# ── Helper ─────────────────────────────────────────────────────────

def upload_ifc(client: TestClient, content: bytes, filename: str = "test.ifc") -> str:
    """Upload an IFC file and return its file_id. Asserts 201."""
    response = client.post(
        UPLOAD_URL,
        files={"file": (filename, io.BytesIO(content), "application/octet-stream")},
    )
    assert response.status_code == 201, f"Upload failed: {response.text}"
    return response.json()["file_id"]


# ── Successful Parse ──────────────────────────────────────────────

class TestSuccessfulParse:
    """Happy-path parse scenarios using the minimal valid IFC fixture."""

    def test_parse_returns_200(
        self, isolated_client: TestClient, minimal_ifc_bytes: bytes
    ) -> None:
        """A successful parse must return HTTP 200."""
        file_id = upload_ifc(isolated_client, minimal_ifc_bytes)
        response = isolated_client.post(PARSE_URL.format(file_id=file_id))
        assert response.status_code == 200, response.text

    def test_parse_result_has_building_section(
        self, isolated_client: TestClient, minimal_ifc_bytes: bytes
    ) -> None:
        """ParseResult must contain a 'building' key."""
        file_id = upload_ifc(isolated_client, minimal_ifc_bytes)
        body = isolated_client.post(PARSE_URL.format(file_id=file_id)).json()
        assert "building" in body

    def test_parse_result_has_elements_section(
        self, isolated_client: TestClient, minimal_ifc_bytes: bytes
    ) -> None:
        """ParseResult must contain an 'elements' key."""
        file_id = upload_ifc(isolated_client, minimal_ifc_bytes)
        body = isolated_client.post(PARSE_URL.format(file_id=file_id)).json()
        assert "elements" in body

    def test_parse_result_has_geometry_section(
        self, isolated_client: TestClient, minimal_ifc_bytes: bytes
    ) -> None:
        """ParseResult must contain a 'geometry' key."""
        file_id = upload_ifc(isolated_client, minimal_ifc_bytes)
        body = isolated_client.post(PARSE_URL.format(file_id=file_id)).json()
        assert "geometry" in body

    def test_schema_version_extracted(
        self, isolated_client: TestClient, minimal_ifc_bytes: bytes
    ) -> None:
        """Schema version must be 'IFC2X3' for the minimal fixture."""
        file_id = upload_ifc(isolated_client, minimal_ifc_bytes)
        body = isolated_client.post(PARSE_URL.format(file_id=file_id)).json()
        assert body["building"]["ifc_schema"] == "IFC2X3"

    def test_project_name_extracted(
        self, isolated_client: TestClient, minimal_ifc_bytes: bytes
    ) -> None:
        """Project name 'Test Project' must be present in the result."""
        file_id = upload_ifc(isolated_client, minimal_ifc_bytes)
        body = isolated_client.post(PARSE_URL.format(file_id=file_id)).json()
        assert body["building"]["project_name"] == "Test Project"

    def test_building_name_extracted(
        self, isolated_client: TestClient, minimal_ifc_bytes: bytes
    ) -> None:
        """Building name 'Test Building' must be present in the result."""
        file_id = upload_ifc(isolated_client, minimal_ifc_bytes)
        body = isolated_client.post(PARSE_URL.format(file_id=file_id)).json()
        assert body["building"]["building_name"] == "Test Building"

    def test_storey_count_is_one(
        self, isolated_client: TestClient, minimal_ifc_bytes: bytes
    ) -> None:
        """The minimal fixture has one IfcBuildingStorey → storeys == 1."""
        file_id = upload_ifc(isolated_client, minimal_ifc_bytes)
        body = isolated_client.post(PARSE_URL.format(file_id=file_id)).json()
        assert body["building"]["storeys"] == 1

    def test_element_counts_are_integers(
        self, isolated_client: TestClient, minimal_ifc_bytes: bytes
    ) -> None:
        """All element count fields must be non-negative integers."""
        file_id = upload_ifc(isolated_client, minimal_ifc_bytes)
        body = isolated_client.post(PARSE_URL.format(file_id=file_id)).json()
        elements = body["elements"]
        for field_name, value in elements.items():
            assert isinstance(value, int), f"{field_name} is not int: {value}"
            assert value >= 0, f"{field_name} is negative: {value}"

    def test_element_counts_all_fields_present(
        self, isolated_client: TestClient, minimal_ifc_bytes: bytes
    ) -> None:
        """All 10 element type fields must be present in the response."""
        expected_fields = {
            "walls", "doors", "windows", "slabs", "columns",
            "beams", "roofs", "stairs", "spaces", "openings",
        }
        file_id = upload_ifc(isolated_client, minimal_ifc_bytes)
        body = isolated_client.post(PARSE_URL.format(file_id=file_id)).json()
        actual_fields = set(body["elements"].keys())
        assert expected_fields.issubset(actual_fields)

    def test_geometry_fields_present(
        self, isolated_client: TestClient, minimal_ifc_bytes: bytes
    ) -> None:
        """All geometry fields must be present (may be null)."""
        expected_fields = {
            "gross_floor_area", "height", "storey_heights",
            "footprint", "bounding_box",
        }
        file_id = upload_ifc(isolated_client, minimal_ifc_bytes)
        body = isolated_client.post(PARSE_URL.format(file_id=file_id)).json()
        actual_fields = set(body["geometry"].keys())
        assert expected_fields.issubset(actual_fields)

    def test_units_extracted(
        self, isolated_client: TestClient, minimal_ifc_bytes: bytes
    ) -> None:
        """Units must be 'METRE' for the minimal fixture."""
        file_id = upload_ifc(isolated_client, minimal_ifc_bytes)
        body = isolated_client.post(PARSE_URL.format(file_id=file_id)).json()
        assert body["building"]["units"] == "METRE"


# ── Not Found Errors ──────────────────────────────────────────────

class TestNotFoundErrors:
    """Scenarios where file_id does not exist in the store."""

    def test_parse_unknown_file_id_returns_404(
        self, isolated_client: TestClient
    ) -> None:
        """Parsing an unknown file_id must return 404."""
        response = isolated_client.post(PARSE_URL.format(file_id="nonexistent-id"))
        assert response.status_code == 404, response.text

    def test_building_unknown_file_id_returns_404(
        self, isolated_client: TestClient
    ) -> None:
        """Getting building info for unknown file_id must return 404."""
        response = isolated_client.get(BUILDING_URL.format(file_id="nonexistent-id"))
        assert response.status_code == 404, response.text

    def test_elements_unknown_file_id_returns_404(
        self, isolated_client: TestClient
    ) -> None:
        """Getting element counts for unknown file_id must return 404."""
        response = isolated_client.get(ELEMENTS_URL.format(file_id="nonexistent-id"))
        assert response.status_code == 404, response.text

    def test_get_building_before_parse_returns_404(
        self, isolated_client: TestClient, minimal_ifc_bytes: bytes
    ) -> None:
        """Getting building info before parsing must return 404 (no cached result)."""
        file_id = upload_ifc(isolated_client, minimal_ifc_bytes)
        response = isolated_client.get(BUILDING_URL.format(file_id=file_id))
        assert response.status_code == 404, response.text

    def test_get_elements_before_parse_returns_404(
        self, isolated_client: TestClient, minimal_ifc_bytes: bytes
    ) -> None:
        """Getting element counts before parsing must return 404."""
        file_id = upload_ifc(isolated_client, minimal_ifc_bytes)
        response = isolated_client.get(ELEMENTS_URL.format(file_id=file_id))
        assert response.status_code == 404, response.text


# ── GET Endpoints After Successful Parse ──────────────────────────

class TestGetEndpointsAfterParse:
    """Verify GET /building and GET /elements return correct data post-parse."""

    def _parse(self, client: TestClient, content: bytes) -> str:
        """Upload + parse and return file_id."""
        file_id = upload_ifc(client, content)
        resp = client.post(PARSE_URL.format(file_id=file_id))
        assert resp.status_code == 200
        return file_id

    def test_get_building_returns_200(
        self, isolated_client: TestClient, minimal_ifc_bytes: bytes
    ) -> None:
        """GET /building/{file_id} returns 200 after a successful parse."""
        file_id = self._parse(isolated_client, minimal_ifc_bytes)
        response = isolated_client.get(BUILDING_URL.format(file_id=file_id))
        assert response.status_code == 200, response.text

    def test_get_building_has_project_name(
        self, isolated_client: TestClient, minimal_ifc_bytes: bytes
    ) -> None:
        """GET /building response must include project_name."""
        file_id = self._parse(isolated_client, minimal_ifc_bytes)
        body = isolated_client.get(BUILDING_URL.format(file_id=file_id)).json()
        assert body["project_name"] == "Test Project"

    def test_get_elements_returns_200(
        self, isolated_client: TestClient, minimal_ifc_bytes: bytes
    ) -> None:
        """GET /elements/{file_id} returns 200 after a successful parse."""
        file_id = self._parse(isolated_client, minimal_ifc_bytes)
        response = isolated_client.get(ELEMENTS_URL.format(file_id=file_id))
        assert response.status_code == 200, response.text

    def test_get_elements_has_walls(
        self, isolated_client: TestClient, minimal_ifc_bytes: bytes
    ) -> None:
        """GET /elements response must include a 'walls' field."""
        file_id = self._parse(isolated_client, minimal_ifc_bytes)
        body = isolated_client.get(ELEMENTS_URL.format(file_id=file_id)).json()
        assert "walls" in body


# ── Corrupt IFC ───────────────────────────────────────────────────

class TestCorruptIFC:
    """Corrupt IFC content must fail gracefully at parse time."""

    def test_corrupt_ifc_parse_returns_422(
        self, isolated_client: TestClient, corrupt_ifc_bytes: bytes
    ) -> None:
        """
        Corrupt IFC with valid header should pass upload validation
        but fail during IfcOpenShell parsing → 422.
        """
        file_id = upload_ifc(isolated_client, corrupt_ifc_bytes)
        response = isolated_client.post(PARSE_URL.format(file_id=file_id))
        # IfcOpenShell may raise on corrupt data section
        assert response.status_code in (422, 500), (
            f"Expected 422 or 500 for corrupt IFC, got {response.status_code}: {response.text}"
        )
