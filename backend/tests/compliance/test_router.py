"""
End-to-end integration tests for the v2 Municipal Rule Engine router.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestComplianceRouterV2:

    def test_list_building_types(self, compliance_client: TestClient) -> None:
        r = compliance_client.get("/api/v1/compliance/building-types")
        assert r.status_code == 200
        types = r.json()
        assert len(types) >= 6
        assert any(t["building_type"] == "residential_house" for t in types)

    def test_classify_endpoint(
        self, compliance_client: TestClient, minimal_parse_result: dict
    ) -> None:
        payload = {"parse_result": minimal_parse_result}
        r = compliance_client.post("/api/v1/compliance/classify", json=payload)
        assert r.status_code == 200
        res = r.json()
        assert res["building_type"] == "residential_house"
        assert res["confidence"] >= 0.90

    def test_check_endpoint_auto_classification(
        self, compliance_client: TestClient, minimal_parse_result: dict, compliant_params: dict
    ) -> None:
        payload = {
            "parse_result": minimal_parse_result,
            "building_params": compliant_params,
        }
        r = compliance_client.post("/api/v1/compliance/check", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert "overall_status" in data
        assert "classification_result" in data
        assert data["classification_result"]["building_type"] == "residential_house"
        assert "residential_house" in data["loaded_rule_sets"]

    def test_check_endpoint_with_override(
        self, compliance_client: TestClient, minimal_parse_result: dict, compliant_params: dict
    ) -> None:
        payload = {
            "parse_result": minimal_parse_result,
            "building_params": compliant_params,
            "override_building_type": "apartment",
        }
        r = compliance_client.post("/api/v1/compliance/check", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert data["classification_result"]["building_type"] == "apartment"
        assert data["classification_result"]["is_override"] is True
        assert "apartment" in data["loaded_rule_sets"]

    def test_list_rules(self, compliance_client: TestClient) -> None:
        r = compliance_client.get("/api/v1/compliance/rules?rules_file=residential_house")
        assert r.status_code == 200
        rules = r.json()
        assert len(rules) >= 15

    def test_get_rule_by_id(self, compliance_client: TestClient) -> None:
        r = compliance_client.get("/api/v1/compliance/rules/BBMP-RES-P001?rules_file=residential_house")
        assert r.status_code == 200
        rule = r.json()
        assert rule["rule_id"] == "BBMP-RES-P001"
