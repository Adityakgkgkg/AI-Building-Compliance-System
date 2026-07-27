"""
Tests for Report Generator & Scoring.
"""

from __future__ import annotations

import pytest

from app.compliance.report.report_generator import ReportGenerator
from app.compliance.report.scoring import compute_score
from app.compliance.schemas import (
    BuildingType,
    ClassificationResult,
    OverallStatus,
    RuleResult,
    RuleStatus,
    Severity,
)


def _rule_res(rid: str, status: RuleStatus, placeholder: bool = False) -> RuleResult:
    return RuleResult(
        rule_id=rid,
        title=f"Rule {rid}",
        category="Test",
        status=status,
        severity=Severity.ERROR,
        is_placeholder=placeholder,
    )


class TestReportGenerator:
    gen = ReportGenerator()

    def test_compute_score_all_passed(self) -> None:
        results = [
            _rule_res("R1", RuleStatus.PASSED),
            _rule_res("R2", RuleStatus.PASSED),
        ]
        assert compute_score(results) == 100

    def test_compute_score_mixed(self) -> None:
        results = [
            _rule_res("R1", RuleStatus.PASSED),
            _rule_res("R2", RuleStatus.FAILED),
        ]
        assert compute_score(results) == 50

    def test_generate_report_structure(self) -> None:
        clf = ClassificationResult(
            building_type=BuildingType.RESIDENTIAL_HOUSE,
            confidence=0.95,
            classification_method="IFC Metadata",
        )
        results = [_rule_res("R1", RuleStatus.PASSED)]
        report = self.gen.generate(results, clf, ["residential_house"])
        assert report.overall_status == OverallStatus.COMPLIANT
        assert report.compliance_score == 100
        assert report.classification_result.building_type == BuildingType.RESIDENTIAL_HOUSE
        assert "residential_house" in report.loaded_rule_sets
