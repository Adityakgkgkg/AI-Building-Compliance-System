"""
Tests for Stage 3: Rule Evaluation Engine & Context Builder.
"""

from __future__ import annotations

import pytest

from app.compliance.rule_engine.context_builder import build_context
from app.compliance.rule_engine.evaluator import RuleEvaluator
from app.compliance.schemas import BuildingParams, RuleStatus


class TestRuleEvaluator:
    evaluator = RuleEvaluator()

    def test_build_context_computes_far_and_coverage(
        self, minimal_parse_result: dict, compliant_params: dict
    ) -> None:
        bp = BuildingParams(**compliant_params)
        ctx = build_context(minimal_parse_result, bp)
        assert ctx["plot_area"] == 250.0
        # gfa=450, plot_area=250 -> FAR = 1.8
        assert ctx["far"] == 1.8
        # footprint=150, plot_area=250 -> coverage = 60%
        assert ctx["ground_coverage_pct"] == 60.0

    def test_evaluate_rule_pass(self) -> None:
        rule = {
            "rule_id": "BBMP-TEST-001",
            "title": "Min Plot Area",
            "category": "Plot",
            "building_types": ["residential_house"],
            "field": "plot_area",
            "operator": "gte",
            "expected_value": 50.0,
            "unit": "sqm",
            "severity": "error",
            "error_message": "Area {actual} < {expected}",
        }
        ctx = {"plot_area": 100.0}
        results = self.evaluator.evaluate_all([rule], ctx)
        assert len(results) == 1
        assert results[0].status == RuleStatus.PASSED

    def test_evaluate_rule_fail(self) -> None:
        rule = {
            "rule_id": "BBMP-TEST-001",
            "title": "Min Plot Area",
            "category": "Plot",
            "building_types": ["residential_house"],
            "field": "plot_area",
            "operator": "gte",
            "expected_value": 50.0,
            "unit": "sqm",
            "severity": "error",
            "error_message": "Area {actual} < {expected}",
        }
        ctx = {"plot_area": 30.0}
        results = self.evaluator.evaluate_all([rule], ctx)
        assert len(results) == 1
        assert results[0].status == RuleStatus.FAILED

    def test_condition_not_met_returns_not_applicable(self) -> None:
        rule = {
            "rule_id": "BBMP-TEST-002",
            "title": "High Rise Setback",
            "category": "Setbacks",
            "building_types": ["apartment"],
            "field": "min_setback",
            "operator": "gte",
            "expected_value": 6.0,
            "unit": "m",
            "severity": "error",
            "conditions": [
                {"field": "is_high_rise", "operator": "eq", "value": True}
            ],
            "error_message": "Setback too small",
        }
        ctx = {"is_high_rise": False, "min_setback": 2.0}
        results = self.evaluator.evaluate_all([rule], ctx)
        assert len(results) == 1
        assert results[0].status == RuleStatus.NOT_APPLICABLE
