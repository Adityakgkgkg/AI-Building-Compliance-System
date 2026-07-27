"""
AI Building Compliance System — Setback Validators

Validators for setback checks:
  - FrontSetbackSmallRoadValidator  (BBMP-RES-S001) road 6–9 m
  - FrontSetbackLargeRoadValidator  (BBMP-RES-S002) road > 9 m
  - RearSetbackStandardValidator    (BBMP-RES-S003) plot ≤ 300 sqm
  - RearSetbackLargeValidator       (BBMP-RES-S004) plot > 300 sqm
  - LeftSetbackValidator            (BBMP-RES-S005)
  - RightSetbackValidator           (BBMP-RES-S006)
  - HighRiseSetbackValidator        (BBMP-RES-S007)
"""

from __future__ import annotations

import logging
from typing import Optional

from app.compliance.validators.base import BaseValidator, BuildingContext, ValidatorResult

logger = logging.getLogger(__name__)


class FrontSetbackSmallRoadValidator(BaseValidator):
    """
    Front setback for roads of 6–9 m width: minimum 1.5 m.

    Rule: BBMP-RES-S001
    Source: BBMP Building Bye-Laws 2003, Table 2, Clause 5.1.
    """

    def validate(self, context: BuildingContext, rule: dict) -> ValidatorResult:
        expected: float = rule["expected_value"]
        unit: str = rule.get("unit", "m")
        road = context.road_width

        # Only applicable if road_width is in [6, 9] m range
        if road is None:
            return ValidatorResult(
                skipped=True,
                expected=expected,
                unit=unit,
                skip_reason="road_width not provided in building_params.",
            )

        if not (6.0 <= road <= 9.0):
            return ValidatorResult(
                not_applicable=True,
                expected=expected,
                unit=unit,
                na_reason=(
                    f"Rule applies to roads 6–9 m wide; "
                    f"abutting road is {road} m."
                ),
            )

        if context.front_setback is None:
            return ValidatorResult(
                skipped=True,
                expected=expected,
                unit=unit,
                skip_reason="front_setback not provided in building_params.",
            )

        actual = context.front_setback
        passed = actual >= expected
        diff = self._numeric_difference(actual, expected)

        if passed:
            return ValidatorResult(
                passed=True,
                actual=actual,
                expected=expected,
                difference=diff,
                unit=unit,
                message=f"Front setback {actual} {unit} meets minimum {expected} {unit} for {road} m road.",
            )

        return ValidatorResult(
            passed=False,
            actual=actual,
            expected=expected,
            difference=diff,
            unit=unit,
            message=self._format_message(rule["message"], actual, expected),
            recommendation=(
                f"Increase front setback by {abs(diff):.2f} {unit} "
                f"to comply with BBMP minimum of {expected} {unit} for {road} m roads."
            ),
        )


class FrontSetbackLargeRoadValidator(BaseValidator):
    """
    Front setback for roads wider than 9 m: minimum 3.0 m.

    Rule: BBMP-RES-S002
    Source: BBMP Building Bye-Laws 2003, Table 2, Clause 5.1.
    """

    def validate(self, context: BuildingContext, rule: dict) -> ValidatorResult:
        expected: float = rule["expected_value"]
        unit: str = rule.get("unit", "m")
        road = context.road_width

        if road is None:
            return ValidatorResult(
                skipped=True,
                expected=expected,
                unit=unit,
                skip_reason="road_width not provided in building_params.",
            )

        if road <= 9.0:
            return ValidatorResult(
                not_applicable=True,
                expected=expected,
                unit=unit,
                na_reason=(
                    f"Rule applies to roads > 9 m wide; "
                    f"abutting road is {road} m."
                ),
            )

        if context.front_setback is None:
            return ValidatorResult(
                skipped=True,
                expected=expected,
                unit=unit,
                skip_reason="front_setback not provided in building_params.",
            )

        actual = context.front_setback
        passed = actual >= expected
        diff = self._numeric_difference(actual, expected)

        if passed:
            return ValidatorResult(
                passed=True,
                actual=actual,
                expected=expected,
                difference=diff,
                unit=unit,
                message=f"Front setback {actual} {unit} meets minimum {expected} {unit} for {road} m road.",
            )

        return ValidatorResult(
            passed=False,
            actual=actual,
            expected=expected,
            difference=diff,
            unit=unit,
            message=self._format_message(rule["message"], actual, expected),
            recommendation=(
                f"Increase front setback by {abs(diff):.2f} {unit} to comply "
                f"with BBMP minimum of {expected} {unit} for roads wider than 9 m."
            ),
        )


class RearSetbackStandardValidator(BaseValidator):
    """
    Rear setback for plots ≤ 300 sqm: minimum 1.0 m.

    Rule: BBMP-RES-S003
    Source: BBMP Building Bye-Laws 2003, Table 3, Clause 5.2.
    """

    def validate(self, context: BuildingContext, rule: dict) -> ValidatorResult:
        expected: float = rule["expected_value"]
        unit: str = rule.get("unit", "m")
        area = context.plot_area

        if area is None:
            return ValidatorResult(
                skipped=True,
                expected=expected,
                unit=unit,
                skip_reason="plot_area not provided in building_params.",
            )

        if area > 300.0:
            return ValidatorResult(
                not_applicable=True,
                expected=expected,
                unit=unit,
                na_reason=(
                    f"Rule applies to plots ≤ 300 sqm; plot area is {area} sqm. "
                    "See BBMP-RES-S004 for larger plots."
                ),
            )

        if context.rear_setback is None:
            return ValidatorResult(
                skipped=True,
                expected=expected,
                unit=unit,
                skip_reason="rear_setback not provided in building_params.",
            )

        actual = context.rear_setback
        passed = actual >= expected
        diff = self._numeric_difference(actual, expected)

        if passed:
            return ValidatorResult(
                passed=True,
                actual=actual,
                expected=expected,
                difference=diff,
                unit=unit,
                message=f"Rear setback {actual} {unit} meets minimum {expected} {unit}.",
            )

        return ValidatorResult(
            passed=False,
            actual=actual,
            expected=expected,
            difference=diff,
            unit=unit,
            message=self._format_message(rule["message"], actual, expected),
            recommendation=(
                f"Increase rear setback by {abs(diff):.2f} {unit} to "
                f"meet the BBMP minimum of {expected} {unit}."
            ),
        )


class RearSetbackLargeValidator(BaseValidator):
    """
    Rear setback for plots > 300 sqm: minimum 2.0 m.

    Rule: BBMP-RES-S004
    Source: BBMP Building Bye-Laws 2003, Table 3, Clause 5.2.
    """

    def validate(self, context: BuildingContext, rule: dict) -> ValidatorResult:
        expected: float = rule["expected_value"]
        unit: str = rule.get("unit", "m")
        area = context.plot_area

        if area is None:
            return ValidatorResult(
                skipped=True,
                expected=expected,
                unit=unit,
                skip_reason="plot_area not provided in building_params.",
            )

        if area <= 300.0:
            return ValidatorResult(
                not_applicable=True,
                expected=expected,
                unit=unit,
                na_reason=(
                    f"Rule applies to plots > 300 sqm; plot area is {area} sqm. "
                    "See BBMP-RES-S003 for standard plots."
                ),
            )

        if context.rear_setback is None:
            return ValidatorResult(
                skipped=True,
                expected=expected,
                unit=unit,
                skip_reason="rear_setback not provided in building_params.",
            )

        actual = context.rear_setback
        passed = actual >= expected
        diff = self._numeric_difference(actual, expected)

        if passed:
            return ValidatorResult(
                passed=True,
                actual=actual,
                expected=expected,
                difference=diff,
                unit=unit,
                message=f"Rear setback {actual} {unit} meets minimum {expected} {unit} for plot > 300 sqm.",
            )

        return ValidatorResult(
            passed=False,
            actual=actual,
            expected=expected,
            difference=diff,
            unit=unit,
            message=self._format_message(rule["message"], actual, expected),
            recommendation=(
                f"Rear setback must be increased by {abs(diff):.2f} {unit}. "
                f"Plots above 300 sqm require a minimum rear setback of {expected} {unit}."
            ),
        )


class LeftSetbackValidator(BaseValidator):
    """
    Left side setback: minimum 1.0 m.

    Rule: BBMP-RES-S005
    Source: BBMP Building Bye-Laws 2003, Table 3, Clause 5.3.
    """

    def validate(self, context: BuildingContext, rule: dict) -> ValidatorResult:
        expected: float = rule["expected_value"]
        unit: str = rule.get("unit", "m")

        if context.left_setback is None:
            return ValidatorResult(
                skipped=True,
                expected=expected,
                unit=unit,
                skip_reason="left_setback not provided in building_params.",
            )

        actual = context.left_setback
        passed = actual >= expected
        diff = self._numeric_difference(actual, expected)

        if passed:
            return ValidatorResult(
                passed=True,
                actual=actual,
                expected=expected,
                difference=diff,
                unit=unit,
                message=f"Left side setback {actual} {unit} meets minimum {expected} {unit}.",
            )

        return ValidatorResult(
            passed=False,
            actual=actual,
            expected=expected,
            difference=diff,
            unit=unit,
            message=self._format_message(rule["message"], actual, expected),
            recommendation=(
                f"Increase left side setback by {abs(diff):.2f} {unit} "
                f"to meet the BBMP minimum of {expected} {unit}."
            ),
        )


class RightSetbackValidator(BaseValidator):
    """
    Right side setback: minimum 1.0 m.

    Rule: BBMP-RES-S006
    Source: BBMP Building Bye-Laws 2003, Table 3, Clause 5.3.
    """

    def validate(self, context: BuildingContext, rule: dict) -> ValidatorResult:
        expected: float = rule["expected_value"]
        unit: str = rule.get("unit", "m")

        if context.right_setback is None:
            return ValidatorResult(
                skipped=True,
                expected=expected,
                unit=unit,
                skip_reason="right_setback not provided in building_params.",
            )

        actual = context.right_setback
        passed = actual >= expected
        diff = self._numeric_difference(actual, expected)

        if passed:
            return ValidatorResult(
                passed=True,
                actual=actual,
                expected=expected,
                difference=diff,
                unit=unit,
                message=f"Right side setback {actual} {unit} meets minimum {expected} {unit}.",
            )

        return ValidatorResult(
            passed=False,
            actual=actual,
            expected=expected,
            difference=diff,
            unit=unit,
            message=self._format_message(rule["message"], actual, expected),
            recommendation=(
                f"Increase right side setback by {abs(diff):.2f} {unit} "
                f"to meet the BBMP minimum of {expected} {unit}."
            ),
        )


class HighRiseSetbackValidator(BaseValidator):
    """
    High-rise setback (all sides): minimum 6.0 m for buildings > G+3.

    Rule: BBMP-RES-S007
    Source: BBMP Building Bye-Laws 2003, Clause 5.4, Table 5.
    """

    def validate(self, context: BuildingContext, rule: dict) -> ValidatorResult:
        expected: float = rule["expected_value"]
        unit: str = rule.get("unit", "m")

        # Only applies to high-rise (> 4 storeys)
        if context.storeys <= 4:
            return ValidatorResult(
                not_applicable=True,
                expected=expected,
                unit=unit,
                na_reason=(
                    f"High-rise setback applies to buildings > 4 storeys; "
                    f"this building has {context.storeys} storey(s)."
                ),
            )

        if context.min_setback_all_sides is None:
            return ValidatorResult(
                skipped=True,
                expected=expected,
                unit=unit,
                skip_reason=(
                    "Cannot compute minimum setback: one or more setback "
                    "values (front/rear/left/right) not provided."
                ),
            )

        actual = context.min_setback_all_sides
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
                    f"Minimum setback {actual} {unit} meets high-rise "
                    f"requirement of {expected} {unit} on all sides."
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
                f"All sides of a high-rise building must have a minimum {expected} {unit} setback. "
                f"The minimum provided setback is {actual} {unit}, which is deficient by "
                f"{abs(diff):.2f} {unit}. Redesign the building footprint to comply."
            ),
        )
