"""
AI Building Compliance System — Access Validators

Validators for road access and electrical clearance:
  - RoadWidthValidator         (BBMP-RES-R001)
  - ElectricalClearanceValidator (BBMP-RES-R002)
"""

from __future__ import annotations

import logging

from app.compliance.validators.base import BaseValidator, BuildingContext, ValidatorResult

logger = logging.getLogger(__name__)


class RoadWidthValidator(BaseValidator):
    """
    Minimum road width for residential construction: 6 m.

    Rule: BBMP-RES-R001
    Source: BBMP Building Bye-Laws 2003, Clause 8.1.
    """

    def validate(self, context: BuildingContext, rule: dict) -> ValidatorResult:
        expected: float = rule["expected_value"]
        unit: str = rule.get("unit", "m")

        if context.road_width is None:
            return ValidatorResult(
                skipped=True,
                expected=expected,
                unit=unit,
                skip_reason="road_width not provided in building_params.",
            )

        actual = context.road_width
        passed = actual >= expected
        diff = self._numeric_difference(actual, expected)

        if passed:
            return ValidatorResult(
                passed=True,
                actual=actual,
                expected=expected,
                difference=diff,
                unit=unit,
                message=(
                    f"Abutting road width {actual} {unit} meets the minimum "
                    f"{expected} {unit} required for residential construction."
                ),
            )

        return ValidatorResult(
            passed=False,
            actual=actual,
            expected=expected,
            difference=diff,
            unit=unit,
            message=self._format_message(rule["message"], actual, expected),
            recommendation=(
                f"The abutting road ({actual} {unit}) does not meet the minimum "
                f"{expected} {unit} required by BBMP for residential construction. "
                "Building permission cannot be granted on this plot."
            ),
        )


class ElectricalClearanceValidator(BaseValidator):
    """
    Minimum clearance from overhead electrical lines: 1.5 m.

    Rule: BBMP-RES-R002
    Source: BBMP Building Bye-Laws 2003, Clause 8.3; KSEB Regulations.
    """

    def validate(self, context: BuildingContext, rule: dict) -> ValidatorResult:
        expected: float = rule["expected_value"]
        unit: str = rule.get("unit", "m")

        if context.electrical_clearance is None:
            return ValidatorResult(
                skipped=True,
                expected=expected,
                unit=unit,
                skip_reason=(
                    "electrical_clearance not provided in building_params. "
                    "Provide clearance value if overhead lines are present near the site."
                ),
            )

        actual = context.electrical_clearance
        passed = actual >= expected
        diff = self._numeric_difference(actual, expected)

        if passed:
            return ValidatorResult(
                passed=True,
                actual=actual,
                expected=expected,
                difference=diff,
                unit=unit,
                message=(
                    f"Electrical line clearance {actual} {unit} meets the "
                    f"minimum safe clearance of {expected} {unit}."
                ),
            )

        return ValidatorResult(
            passed=False,
            actual=actual,
            expected=expected,
            difference=diff,
            unit=unit,
            message=self._format_message(rule["message"], actual, expected),
            recommendation=(
                f"Electrical clearance is deficient by {abs(diff):.2f} {unit}. "
                "Contact BESCOM for line shifting or modify the building layout "
                f"to maintain at least {expected} {unit} clearance from overhead lines."
            ),
        )
