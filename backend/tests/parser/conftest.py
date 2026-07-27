"""
Shared pytest fixtures for the IFC Parser test suite.

Provides:
    - client: FastAPI TestClient with a fresh, isolated in-memory store per test
    - minimal_ifc_bytes: Bytes of a minimal valid IFC2X3 file (no geometry)
    - corrupt_ifc_bytes: Bytes that look like IFC but contain garbage data
    - non_ifc_bytes: Bytes with an entirely wrong header (not IFC at all)
    - tmp_ifc_file: A real on-disk IFC file (pathlib.Path) for file_loader tests
"""

from __future__ import annotations

import io
import textwrap
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# ── Minimal valid IFC content ─────────────────────────────────────
# A stripped-down IFC2X3 file that IfcOpenShell can open and that
# contains exactly one IfcProject, one IfcBuilding, one IfcBuildingStorey.
_MINIMAL_IFC_CONTENT = textwrap.dedent("""\
    ISO-10303-21;
    HEADER;
    FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
    FILE_NAME('test.ifc','2024-01-01T00:00:00',('Test Author'),('Test Org'),'IfcOpenShell','IfcOpenShell','');
    FILE_SCHEMA(('IFC2X3'));
    ENDSEC;
    DATA;
    #1=IFCORGANIZATION($,'Test Org',$,$,$);
    #2=IFCPERSON($,'Doe','John',$,$,$,$,$);
    #3=IFCPERSONANDORGANIZATION(#2,#1,$);
    #4=IFCAPPLICATION(#1,'1.0','Test App','TestApp');
    #5=IFCOWNERHISTORY(#3,#4,$,.NOCHANGE.,$,$,$,0);
    #6=IFCDIMENSIONALEXPONENTS(0,0,0,0,0,0,0);
    #7=IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.);
    #8=IFCSIUNIT(*,.AREAUNIT.,$,.SQUARE_METRE.);
    #9=IFCSIUNIT(*,.VOLUMEUNIT.,$,.CUBIC_METRE.);
    #10=IFCUNITASSIGNMENT((#7,#8,#9));
    #11=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.E-05,#12,$);
    #12=IFCAXIS2PLACEMENT3D(#13,$,$);
    #13=IFCCARTESIANPOINT((0.,0.,0.));
    #14=IFCPROJECT('1hqIFTRfnCAxqsetlFXmMo',#5,'Test Project',$,$,$,$,(#11),#10);
    #15=IFCLOCALPLACEMENT($,#12);
    #16=IFCSITE('1hqIFTRfnCAxqsetlFXmMp',#5,'Test Site',$,$,#15,$,$,.ELEMENT.,$,$,$,$,$);
    #17=IFCLOCALPLACEMENT(#15,#12);
    #18=IFCBUILDING('1hqIFTRfnCAxqsetlFXmMq',#5,'Test Building','A test building',$,#17,$,$,.ELEMENT.,$,$,$);
    #19=IFCLOCALPLACEMENT(#17,#12);
    #20=IFCBUILDINGSTOREY('1hqIFTRfnCAxqsetlFXmMr',#5,'Ground Floor',$,$,#19,$,$,.ELEMENT.,0.);
    #21=IFCRELAGGREGATES('1hqIFTRfnCAxqsetlFXmMs',#5,$,$,#14,(#16));
    #22=IFCRELAGGREGATES('1hqIFTRfnCAxqsetlFXmMt',#5,$,$,#16,(#18));
    #23=IFCRELAGGREGATES('1hqIFTRfnCAxqsetlFXmMu',#5,$,$,#18,(#20));
    ENDSEC;
    END-ISO-10303-21;
""")

_MINIMAL_IFC_BYTES: bytes = _MINIMAL_IFC_CONTENT.encode("utf-8")

# IFC header present but body is garbage — IfcOpenShell will fail to parse
_CORRUPT_IFC_BYTES: bytes = (
    b"ISO-10303-21;\nHEADER;\n"
    b"FILE_SCHEMA(('IFC4'));\nENDSEC;\nDATA;\n"
    b"#1=TOTALLY_INVALID_GARBAGE_DATA_@@@@;\n"
    b"ENDSEC;\nEND-ISO-10303-21;\n"
)

# Completely wrong file type (PDF-like header)
_NON_IFC_BYTES: bytes = b"%PDF-1.4 Some PDF content that is not IFC at all\n"


# ── Fixtures ──────────────────────────────────────────────────────

@pytest.fixture
def minimal_ifc_bytes() -> bytes:
    """Return bytes for a minimal but structurally valid IFC2X3 file."""
    return _MINIMAL_IFC_BYTES


@pytest.fixture
def corrupt_ifc_bytes() -> bytes:
    """Return bytes that have a valid IFC header but corrupt DATA section."""
    return _CORRUPT_IFC_BYTES


@pytest.fixture
def non_ifc_bytes() -> bytes:
    """Return bytes with an entirely non-IFC header (e.g. PDF)."""
    return _NON_IFC_BYTES


@pytest.fixture
def tmp_ifc_file(tmp_path: Path, minimal_ifc_bytes: bytes) -> Path:
    """Write a minimal IFC file to a temporary directory and return its path."""
    ifc_path = tmp_path / "test_building.ifc"
    ifc_path.write_bytes(minimal_ifc_bytes)
    return ifc_path


@pytest.fixture
def client() -> TestClient:
    """
    Return a FastAPI TestClient with a fresh isolated in-memory store.

    Each test gets a clean ParsedFileStore so tests do not share state.
    The module-level ``file_store`` singleton is patched for the duration
    of each test via monkeypatching in individual tests, or the service
    is instantiated with a fresh store per-test where needed.
    """
    from main import app
    return TestClient(app)


@pytest.fixture
def isolated_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """
    TestClient backed by a fresh ParsedFileStore and using tmp_path for uploads.

    Patches:
        - app.parser.models.file_store      -> fresh ParsedFileStore
        - app.parser.router._service        -> ParserService(store=fresh_store)
        - IFCFileLoader._upload_root        -> tmp_path / 'ifc'
    """
    import sys  # noqa: PLC0415

    # Must import main.app first to ensure all modules land in sys.modules
    from main import app  # noqa: PLC0415
    from app.parser.models import ParsedFileStore  # noqa: PLC0415
    from app.parser.service import ParserService  # noqa: PLC0415
    from app.parser.file_loader import IFCFileLoader  # noqa: PLC0415
    import app.parser.models as models_module  # noqa: PLC0415

    # Retrieve the router module by its sys.modules key.
    # We cannot use "import app.parser.router" directly because
    # app.parser.__init__ shadows "router" with the re-exported APIRouter object.
    router_module = sys.modules["app.parser.router"]

    # Fresh in-memory store — no constructor arguments needed
    fresh_store = ParsedFileStore()

    # Redirect file writes to tmp_path so tests don't pollute uploads/
    ifc_upload_root = tmp_path / "ifc"
    ifc_upload_root.mkdir(parents=True, exist_ok=True)

    fresh_service = ParserService(store=fresh_store)
    # Override the loader's upload root on the fresh service instance
    fresh_service._loader._upload_root = ifc_upload_root

    monkeypatch.setattr(models_module, "file_store", fresh_store)
    monkeypatch.setattr(router_module, "_service", fresh_service)

    return TestClient(app)
