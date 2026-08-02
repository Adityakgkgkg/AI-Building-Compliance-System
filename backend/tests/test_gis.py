"""
GIS Context Intelligence Engine Unit & Integration Tests
========================================================
Validates spatial indexing, detector accuracy, manifest lineage,
execution performance (< 200 ms), and FastAPI GIS endpoints.
"""

import time
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from main import app
from app.gis.dataset_manager import DatasetManager
from app.gis.context_engine import UrbanContextEngine
from app.gis.schemas import GISContextRequest
from app.gis.ward_detector import WardDetector
from app.gis.zone_detector import ZoneDetector
from app.gis.road_detector import RoadDetector
from app.gis.lake_detector import LakeDetector
from app.gis.airport_detector import AirportDetector
from app.gis.flood_detector import FloodDetector


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module", autouse=True)
def setup_gis_datasets():
    dm = DatasetManager.get_instance()
    dm.initialize()
    return dm


def test_dataset_manager_initialization(setup_gis_datasets):
    dm = setup_gis_datasets
    assert dm.is_loaded is True
    assert dm.manifest_data is not None
    assert "wards" in dm.spatial_indexes
    assert "roads" in dm.spatial_indexes
    assert "lakes" in dm.spatial_indexes


def test_ward_detector_jayanagar():
    # Jayanagar coordinates: ~ 12.9250 N, 77.5938 E
    ward_res = WardDetector.detect_ward(12.9250, 77.5938)
    assert ward_res.city == "Bangalore"
    assert ward_res.authority == "BBMP"
    assert ward_res.ward_name in ["Jayanagar", "Central Bangalore Ward"]
    assert ward_res.citation is not None


def test_zone_detector_jayanagar():
    zone_res = ZoneDetector.detect_zone("Jayanagar", "167")
    assert zone_res.zone == "South Zone"
    assert zone_res.ward == "Jayanagar"


def test_road_detector():
    # Location near ORR: 12.920, 77.620
    road_res = RoadDetector.detect_nearest_road(12.920, 77.620)
    assert road_res.road_name != ""
    assert road_res.road_width > 0.0
    assert road_res.distance_meters >= 0.0


def test_lake_detector_bellandur():
    # Bellandur lake area: 12.935, 77.670
    lake_res = LakeDetector.detect_lake_proximity(12.935, 77.670)
    assert lake_res.nearest_lake_name != ""
    assert lake_res.lake_distance >= 0.0
    assert isinstance(lake_res.lake_buffer, bool)


def test_airport_detector():
    # Near HAL airport: 12.955, 77.660
    ap_res = AirportDetector.detect_airport_restriction(12.955, 77.660)
    assert ap_res.airport_zone is True
    assert ap_res.airport_height_limit is not None


def test_context_engine_performance():
    # Performance benchmark test (< 200 ms requirement)
    req = GISContextRequest(latitude=12.9250, longitude=77.5938)
    start_t = time.perf_counter()
    resp = UrbanContextEngine.evaluate_context(req)
    duration_ms = (time.perf_counter() - start_t) * 1000.0

    assert resp.city == "Bangalore"
    assert resp.authority == "BBMP"
    assert len(resp.approval_report_text) > 50
    assert len(resp.citations) > 0
    assert duration_ms < 200.0, f"Spatial evaluation took {duration_ms:.2f} ms (must be < 200 ms)"


def test_api_context_endpoint(client):
    response = client.post(
        "/api/v1/gis/context",
        json={"latitude": 12.9250, "longitude": 77.5938}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["city"] == "Bangalore"
    assert data["authority"] == "BBMP"
    assert "zone" in data
    assert "ward" in data
    assert "road_name" in data
    assert "road_width" in data
    assert "lake_distance" in data
    assert "approval_report_text" in data
    assert "citations" in data


def test_api_individual_endpoints(client):
    w_resp = client.get("/api/v1/gis/ward?lat=12.9250&lon=77.5938")
    assert w_resp.status_code == 200
    assert "ward_name" in w_resp.json()

    z_resp = client.get("/api/v1/gis/zone?lat=12.9250&lon=77.5938")
    assert z_resp.status_code == 200
    assert "zone" in z_resp.json()

    r_resp = client.get("/api/v1/gis/road?lat=12.9250&lon=77.5938")
    assert r_resp.status_code == 200
    assert "road_width" in r_resp.json()

    l_resp = client.get("/api/v1/gis/lake?lat=12.9250&lon=77.5938")
    assert l_resp.status_code == 200
    assert "lake_distance" in l_resp.json()

    m_resp = client.get("/api/v1/gis/manifest")
    assert m_resp.status_code == 200
    assert "datasets" in m_resp.json()
