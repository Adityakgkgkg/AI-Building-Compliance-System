"""
AI Building Compliance System — Plot Validators

Validators for plot-level checks:
  - PlotAreaValidator     (BBMP-RES-P001)
  - PlotWidthValidator    (BBMP-RES-P002)
  - PlotDepthValidator    (BBMP-RES-P003)
"""

from __future__ import annotations

import logging

from app.compliance.validators.base import BaseValidator, BuildingContext, ValidatorResult

logger = logging.getLogger(__name__)


class PlotAreaValidator(BaseValidator):
    """
    Validates that the plot area meets the minimum required by BBMP.

    Rule: BBMP-RES-P001 — Minimum Plot Area (50 sqm).
    Source: BBMP Building Bye-Laws 2003, Table 1, Clause 3.1.
    """

    def validate(self, context: BuildingContext, rule: dict) -> ValidatorResult:
        expected: float = rule["expected_value"]
        unit: str = rule.get("unit", "sqm")

        if context.plot_area is None:
            return ValidatorResult(
                skipped=True,
                expected=expected,
                unit=unit,
                skip_reason="plot_area not provided in building_params.",
            )

        actual = context.plot_area
        passed = actual >= expected
        diff = self._numeric_difference(actual, expected)

        if passed:
            return ValidatorResult(
                passed=True,
                actual=actual,
                expected=expected,
                difference=diff,
                unit=unit,
                message=f"Plot area {actual} {unit} meets minimum {expected} {unit}.",
            )

        return ValidatorResult(
            passed=False,
            actual=actual,
            expected=expected,
            difference=diff,
            unit=unit,
            message=self._format_message(rule["message"], actual, expected),
            recommendation=(
                f"Increase plot area by at least {abs(diff):.2f} {unit} "
                f"to meet the minimum requirement of {expected} {unit}."
            ),
        )


class PlotWidthValidator(BaseValidator):
    """
    Validates that the plot width meets the minimum required by BBMP.

    Rule: BBMP-RES-P002 — Minimum Plot Width (4.5 m).
    Source: BBMP Building Bye-Laws 2003, Table 1, Clause 3.2.
    """

    def validate(self, context: BuildingContext, rule: dict) -> ValidatorResult:
        expected: float = rule["expected_value"]
        unit: str = rule.get("unit", "m")

        if context.plot_width is None:
            return ValidatorResult(
                skipped=True,
                expected=expected,
                unit=unit,
                skip_reason="plot_width not provided in building_params.",
            )

        actual = context.plot_width
        passed = actual >= expected
        diff = self._numeric_difference(actual, expected)

        if passed:
            return ValidatorResult(
                passed=True,
                actual=actual,
                expected=expected,
                difference=diff,
                unit=unit,
                message=f"Plot width {actual} {unit} meets minimum {expected} {unit}.",
            )

        return ValidatorResult(
            passed=False,
            actual=actual,
            expected=expected,
            difference=diff,
            unit=unit,
            message=self._format_message(rule["message"], actual, expected),
            recommendation=(
                f"Plot width is deficient by {abs(diff):.2f} {unit}. "
                "Consider plot amalgamation or layout redesign."
            ),
        )


class PlotDepthValidator(BaseValidator):
    """
    Validates that the plot depth meets the minimum required by BBMP.

    Rule: BBMP-RES-P003 — Minimum Plot Depth (9 m).
    Source: BBMP Building Bye-Laws 2003, Table 1, Clause 3.3.
    """

    def validate(self, context: BuildingContext, rule: dict) -> ValidatorResult:
        expected: float = rule["expected_value"]
        unit: str = rule.get("unit", "m")

        if context.plot_depth is None:
            return ValidatorResult(
                skipped=True,
                expected=expected,
                unit=unit,
                skip_reason="plot_depth not provided in building_params.",
            )

        actual = context.plot_depth
        passed = actual >= expected
        diff = self._numeric_difference(actual, expected)

        if passed:
            return ValidatorResult(
                passed=True,
                actual=actual,
                expected=expected,
                difference=diff,
                unit=unit,
                message=f"Plot depth {actual} {unit} meets minimum {expected} {unit}.",
            )

        return ValidatorResult(
            passed=False,
            actual=actual,
            expected=expected,
            difference=diff,
            unit=unit,
            message=self._format_message(rule["message"], actual, expected),
            recommendation=(
                f"Plot depth is deficient by {abs(diff):.2f} {unit}. "
                "Minimum depth of 9 m is required for habitable space planning."
            ),
        )
