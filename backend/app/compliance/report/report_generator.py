"""
AI Building Compliance System — Report Generator v2

Assembles the final ComplianceReport from:
  - ClassificationResult (Stage 1)
  - List of loaded rule set names (Stage 2)
  - List of RuleResult (Stage 3)

Uses violation_analyzer.py and scoring.py as pure sub-functions.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.compliance.report.scoring import compute_score
from app.compliance.report.violation_analyzer import analyze
from app.compliance.schemas import (
    ClassificationResult,
    ComplianceReport,
    ComplianceSummary,
    OverallStatus,
    ReportMetadata,
    RuleResult,
    RuleStatus,
)

logger = logging.getLogger(__name__)

_ENGINE_VERSION = "2.0.0"


class ReportGenerator:
    """Assembles the ComplianceReport from stage outputs."""

    def generate(
        self,
        results: List[RuleResult],
        classification: Optional[ClassificationResult],
        loaded_rule_sets: List[str],
        building_params: Optional[Dict[str, Any]] = None,
        file_id: Optional[str] = None,
    ) -> ComplianceReport:
        """
        Build and return the complete ComplianceReport.

        Args:
            results:          RuleResult list from the evaluator.
            classification:   Stage 1 output.
            loaded_rule_sets: Names of rule files loaded in Stage 2.
            building_params:  Snapshot of the caller-supplied params.
            file_id:          Source IFC file UUID (if applicable).

        Returns:
            ComplianceReport — the stable downstream contract.
        """
        (
            violations, warnings, passed_rules, failed_rules,
            not_applicable, skipped, category_results,
        ) = analyze(results)

        score = compute_score(results)
        overall_status = self._determine_status(
            n_failed=len(violations),
            n_warnings=len(warnings),
            n_passed=len(passed_rules),
            n_na=len(not_applicable),
            n_skipped=len(skipped),
            total=len(results),
        )

        n_placeholders = sum(1 for r in results if r.is_placeholder)

        summary = ComplianceSummary(
            total_rules=len(results),
            passed=len(passed_rules),
            failed=len(violations),
            warnings=len(warnings),
            not_applicable=len(not_applicable),
            skipped=len(skipped),
            placeholders=n_placeholders,
        )

        building_type_label = (
            classification.building_type.value.replace("_", " ").title()
            if classification
            else "Unknown"
        )

        metadata = ReportMetadata(
            authority="BBMP",
            bye_laws="2003",
            building_type=building_type_label,
            rules_file=", ".join(loaded_rule_sets) if loaded_rule_sets else None,
            engine_version=_ENGINE_VERSION,
            checked_at=datetime.now(timezone.utc),
            file_id=file_id,
        )

        logger.info(
            "Report: status=%s score=%d violations=%d warnings=%d passed=%d",
            overall_status.value, score,
            len(violations), len(warnings), len(passed_rules),
        )

        return ComplianceReport(
            overall_status=overall_status,
            compliance_score=score,
            summary=summary,
            category_results=category_results,
            classification_result=classification,
            loaded_rule_sets=loaded_rule_sets,
            violations=violations,
            warnings=warnings,
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            not_applicable_rules=not_applicable,
            metadata=metadata,
            building_params_snapshot=building_params,
        )

    @staticmethod
    def _determine_status(
        n_failed: int,
        n_warnings: int,
        n_passed: int,
        n_na: int,
        n_skipped: int,
        total: int,
    ) -> OverallStatus:
        evaluable = total - n_na - n_skipped
        if evaluable == 0:
            return OverallStatus.INSUFFICIENT_DATA
        if n_failed > 0:
            return OverallStatus.NON_COMPLIANT
        if n_warnings > 0:
            return OverallStatus.CONDITIONALLY_COMPLIANT
        return OverallStatus.COMPLIANT
