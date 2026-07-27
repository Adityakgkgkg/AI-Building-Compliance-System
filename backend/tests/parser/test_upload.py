"""
Tests for POST /api/v1/parser/upload

Covers:
    - Successful .ifc upload → 201 + file_id
    - Empty file → 400
    - Wrong extension (.pdf, .dxf, no ext) → 422
    - No filename → 400
    - Oversized file → 413
    - Non-IFC content with .ifc extension → 422 (header check)
"""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

UPLOAD_URL = "/api/v1/parser/upload"


class TestSuccessfulUpload:
    """Happy-path upload scenarios."""

    def test_valid_ifc_returns_201(
        self, isolated_client: TestClient, minimal_ifc_bytes: bytes
    ) -> None:
        """A valid .ifc file should return HTTP 201 with a file_id."""
        response = isolated_client.post(
            UPLOAD_URL,
            files={"file": ("building.ifc", io.BytesIO(minimal_ifc_bytes), "application/octet-stream")},
        )
        assert response.status_code == 201, response.text

    def test_response_contains_file_id(
        self, isolated_client: TestClient, minimal_ifc_bytes: bytes
    ) -> None:
        """Response must include a non-empty file_id UUID string."""
        response = isolated_client.post(
            UPLOAD_URL,
            files={"file": ("building.ifc", io.BytesIO(minimal_ifc_bytes), "application/octet-stream")},
        )
        body = response.json()
        assert "file_id" in body
        assert len(body["file_id"]) == 36  # UUID4 canonical format

    def test_response_schema(
        self, isolated_client: TestClient, minimal_ifc_bytes: bytes
    ) -> None:
        """Response must include filename and status='uploaded'."""
        response = isolated_client.post(
            UPLOAD_URL,
            files={"file": ("my_building.ifc", io.BytesIO(minimal_ifc_bytes), "application/octet-stream")},
        )
        body = response.json()
        assert body["filename"] == "my_building.ifc"
        assert body["status"] == "uploaded"

    def test_file_id_is_unique_per_upload(
        self, isolated_client: TestClient, minimal_ifc_bytes: bytes
    ) -> None:
        """Two uploads should produce different file_ids."""
        def upload():
            return isolated_client.post(
                UPLOAD_URL,
                files={"file": ("building.ifc", io.BytesIO(minimal_ifc_bytes), "application/octet-stream")},
            ).json()["file_id"]

        assert upload() != upload()


class TestEmptyFile:
    """Empty file upload scenarios."""

    def test_empty_file_returns_400(
        self, isolated_client: TestClient
    ) -> None:
        """An empty file (0 bytes) must be rejected with 400."""
        response = isolated_client.post(
            UPLOAD_URL,
            files={"file": ("empty.ifc", io.BytesIO(b""), "application/octet-stream")},
        )
        assert response.status_code == 400, response.text

    def test_empty_file_error_message(
        self, isolated_client: TestClient
    ) -> None:
        """Error detail must mention the file is empty."""
        response = isolated_client.post(
            UPLOAD_URL,
            files={"file": ("empty.ifc", io.BytesIO(b""), "application/octet-stream")},
        )
        assert "empty" in response.json()["detail"].lower()


class TestWrongExtension:
    """Invalid extension scenarios."""

    @pytest.mark.parametrize("filename", [
        "document.pdf",
        "plan.dxf",
        "spreadsheet.xlsx",
        "image.png",
        "archive.zip",
    ])
    def test_wrong_extension_returns_422(
        self, isolated_client: TestClient, minimal_ifc_bytes: bytes, filename: str
    ) -> None:
        """Non-.ifc extensions must be rejected with 422."""
        response = isolated_client.post(
            UPLOAD_URL,
            files={"file": (filename, io.BytesIO(minimal_ifc_bytes), "application/octet-stream")},
        )
        assert response.status_code == 422, f"Expected 422 for {filename}, got {response.status_code}"

    def test_no_extension_returns_422(
        self, isolated_client: TestClient, minimal_ifc_bytes: bytes
    ) -> None:
        """A filename with no extension must be rejected with 422."""
        response = isolated_client.post(
            UPLOAD_URL,
            files={"file": ("noextension", io.BytesIO(minimal_ifc_bytes), "application/octet-stream")},
        )
        assert response.status_code == 422, response.text


class TestNonIFCContent:
    """Content validation — correct extension but wrong/corrupt content."""

    def test_pdf_content_with_ifc_extension_returns_422(
        self, isolated_client: TestClient, non_ifc_bytes: bytes
    ) -> None:
        """A PDF file renamed to .ifc must be rejected (header check)."""
        response = isolated_client.post(
            UPLOAD_URL,
            files={"file": ("sneaky.ifc", io.BytesIO(non_ifc_bytes), "application/octet-stream")},
        )
        assert response.status_code == 422, response.text

    def test_invalid_header_error_message(
        self, isolated_client: TestClient, non_ifc_bytes: bytes
    ) -> None:
        """Error message should mention IFC or ISO-10303."""
        response = isolated_client.post(
            UPLOAD_URL,
            files={"file": ("sneaky.ifc", io.BytesIO(non_ifc_bytes), "application/octet-stream")},
        )
        detail = response.json()["detail"].lower()
        assert "ifc" in detail or "iso-10303" in detail


class TestOversizedFile:
    """File size limit enforcement."""

    def test_oversized_file_returns_413(
        self, isolated_client: TestClient, minimal_ifc_bytes: bytes,
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A file exceeding _max_bytes on the loader must return 413."""
        import sys  # noqa: PLC0415

        # Ensure the router module is loaded
        from main import app  # noqa: F401, PLC0415

        router_module = sys.modules["app.parser.router"]
        service = router_module._service
        # Set the size limit to 1 byte so any real IFC file triggers 413
        monkeypatch.setattr(service._loader, "_max_bytes", 1)

        response = isolated_client.post(
            UPLOAD_URL,
            files={"file": ("building.ifc", io.BytesIO(minimal_ifc_bytes), "application/octet-stream")},
        )
        assert response.status_code == 413, response.text
