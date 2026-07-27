"""
Shared pytest fixtures for the v2 Municipal Rule Engine test suite.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def minimal_parse_result() -> dict:
    """Valid ParseResult JSON for a 3-storey (G+2) residential building."""
    return {
        "building": {
            "project_name": "Test Residence",
            "building_name": "Block A",
            "site_name": "Plot 10, Bengaluru",
            "description": "Independent residential villa",
            "ifc_schema": "IFC2X3",
            "storeys": 3,
            "units": "METRE",
            "owner": "Test Owner",
        },
        "elements": {
            "walls": 40,
            "doors": 12,
            "windows": 18,
            "slabs": 3,
            "columns": 12,
            "beams": 20,
            "roofs": 1,
            "stairs": 1,
            "spaces": 9,
            "openings": 5,
        },
        "geometry": {
            "gross_floor_area": 450.0,
            "height": 10.5,
            "storey_heights": [3.5, 3.5, 3.5],
            "footprint": 150.0,
            "bounding_box": {
                "min_x": 0.0,
                "min_y": 0.0,
                "min_z": 0.0,
                "max_x": 15.0,
                "max_y": 10.0,
                "max_z": 10.5,
            },
        },
    }


@pytest.fixture
def apartment_parse_result() -> dict:
    """ParseResult for a 6-storey Apartment Complex."""
    return {
        "building": {
            "project_name": "Sunrise Heights",
            "building_name": "Block B",
            "site_name": "Whitefield, Bengaluru",
            "description": "Multi-dwelling residential flat complex",
            "ifc_schema": "IFC4",
            "storeys": 6,
            "units": "METRE",
        },
        "elements": {
            "walls": 120,
            "doors": 45,
            "windows": 60,
            "slabs": 6,
            "columns": 24,
            "stairs": 2,
            "spaces": 25,
        },
        "geometry": {
            "gross_floor_area": 1800.0,
            "height": 21.0,
            "footprint": 300.0,
        },
    }


@pytest.fixture
def compliant_params() -> dict:
    return {
        "plot_area": 250.0,
        "plot_width": 15.0,
        "plot_depth": 17.0,
        "road_width": 9.0,
        "front_setback": 2.0,
        "rear_setback": 1.5,
        "left_setback": 1.2,
        "right_setback": 1.2,
        "zone": "residential",
        "building_use": "residential",
        "num_units": 1,
        "parking_spaces_provided": 2,
        "garage_width": 2.5,
        "garage_length": 5.0,
        "electrical_clearance": 2.0,
    }


@pytest.fixture
def compliance_client() -> TestClient:
    from main import app
    return TestClient(app)
