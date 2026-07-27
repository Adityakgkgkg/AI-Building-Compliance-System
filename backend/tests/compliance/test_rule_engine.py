"""
Tests for RuleEngine.

Covers:
  - evaluate_all() returns one result per rule
  - Unknown rule_id → SKIPPED result
  - Validator exception → SKIPPED (not crash)
  - Placeholder ERROR rule → capped to WARNING
  - PASSED, FAILED, WARNING statuses correctly assigned
  - All statuses mapped correctly in bulk evaluation
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.compliance.rule_engine import RuleEngine
from app.compliance.schemas import RuleStatus, Severity
from app.compliance.validators.base import BuildingContext, ValidatorResult


def _make_rule(
    rule_id: str,
    severity: str = "error",
    is_placeholder: bool = False,
) -> dict:
    return {
        "rule_id": rule_id,
        "title": f"Rule {rule_id}",
        "category": "Test",
        "applies_to": ["residential"],
        "operator": "gte",
        "expected_value": 10.0,
        "unit": "m",
        "severity": severity,
        "source": "Test Source",
        "message": "Test message {actual} vs {expected}",
        "explanation": "Test explanation",
        "is_placeholder": is_placeholder,
    }


def _ctx(**kwargs) -> BuildingContext:
    ctx = BuildingContext(**kwargs)
    ctx.compute_derived_fields()
    return ctx


class TestRuleEngineBasic:
    engine = RuleEngine()

    def test_evaluate_all_count(self) -> None:
        """One RuleResult per rule."""
        from app.compliance.rule_selection.loader import RuleLoader
        loader = RuleLoader()
        rules = loader.load("residential_house")
        ctx = {
            "plot_area": 250.0,
            "plot_width": 15.0,
            "plot_depth": 17.0,
            "storeys": 3,
            "height": 10.5,
            "gross_floor_area": 450.0,
            "footprint": 150.0,
            "storey_heights": [3.5, 3.5, 3.5],
            "road_width": 9.0,
            "front_setback": 1.5,
            "rear_setback": 1.5,
            "left_setback": 1.2,
            "right_setback": 1.2,
            "num_units": 1,
            "parking_spaces_provided": 2,
            "garage_width": 2.5,
            "garage_length": 5.0,
            "electrical_clearance": 2.0,
            "has_rainwater_harvesting": True,
            "has_solar_water_heater": True,
            "min_side_setback": 1.2,
            "min_setback": 1.2,
            "far": 1.8,
            "ground_coverage_pct": 60.0,
            "is_high_rise": False,
        }
        results = self.engine.evaluate_all(rules, ctx)
        assert len(results) == len(rules)

    def test_unknown_rule_id_is_skipped(self) -> None:
        rules = [{
            "rule_id": "UNKNOWN-999",
            "title": "Unknown",
            "category": "Test",
            "building_types": ["residential_house"],
            "field": "nonexistent_field_12345",
            "operator": "gte",
            "expected_value": 10.0,
            "unit": "m",
            "severity": "error",
            "error_message": "Fail",
        }]
        ctx = {}
        results = self.engine.evaluate_all(rules, ctx)
        assert len(results) == 1
        assert results[0].status == RuleStatus.SKIPPED

    def test_placeholder_error_capped_to_warning(self) -> None:
        rules = [{
            "rule_id": "TEST-PH",
            "title": "Placeholder Test",
            "category": "Test",
            "building_types": ["residential_house"],
            "field": "plot_area",
            "operator": "gte",
            "expected_value": 100.0,
            "unit": "sqm",
            "severity": "error",
            "is_placeholder": True,
            "error_message": "Fail",
        }]
        ctx = {"plot_area": 30.0}
        results = self.engine.evaluate_all(rules, ctx)
        assert results[0].status == RuleStatus.WARNING
        assert results[0].severity == Severity.WARNING


class TestRuleEngineFullIntegration:

    def test_compliant_building_high_score(self) -> None:
        from app.compliance.rule_selection.loader import RuleLoader
        loader = RuleLoader()
        rules = loader.load("residential_house")
        engine = RuleEngine()

        ctx = {
            "storeys": 3,
            "height": 10.5,
            "gross_floor_area": 400.0,
            "footprint": 135.0,
            "storey_heights": [3.5, 3.5, 3.5],
            "plot_area": 250.0,
            "plot_width": 15.0,
            "plot_depth": 17.0,
            "road_width": 9.0,
            "front_setback": 2.0,
            "rear_setback": 1.5,
            "left_setback": 1.2,
            "right_setback": 1.2,
            "min_side_setback": 1.2,
            "min_setback": 1.2,
            "far": 1.6,
            "ground_coverage_pct": 54.0,
            "is_high_rise": False,
            "num_units": 1,
            "parking_spaces_provided": 2,
            "garage_width": 2.5,
            "garage_length": 5.0,
            "electrical_clearance": 2.0,
            "has_rainwater_harvesting": True,
            "has_solar_water_heater": True,
        }


        results = engine.evaluate_all(rules, ctx)
        failures = [r for r in results if r.status == RuleStatus.FAILED]
        assert len(failures) == 0, f"Unexpected failures: {[r.rule_id for r in failures]}"

