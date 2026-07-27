"""
AI Building Compliance System — Geometry Validators

Validators for building geometry checks:
  - HeightValidator            (BBMP-RES-G001) max height 15 m for G+3
  - StoreyValidator            (BBMP-RES-G002) max 4 storeys standard
  - StoreyHeightValidator      (BBMP-RES-G003) min floor height 2.75 m
  - HighRiseEligibilityValidator (BBMP-RES-G004) road width for high-rise
  - FARSmallPlotValidator      (BBMP-RES-F001) FAR ≤ 300 sqm
  - FARMediumPlotValidator     (BBMP-RES-F002) FAR 300–500 sqm
  - FARLargePlotValidator      (BBMP-RES-F003) FAR > 500 sqm
  - GroundCoverageSmallValidator  (BBMP-RES-C001) coverage ≤ 300 sqm
  - GroundCoverageMediumValidator (BBMP-RES-C002) coverage 300–500 sqm
  - GroundCoverageLargeValidator  (BBMP-RES-C003) coverage > 500 sqm
"""

from __future__ import annotations

import logging
from typing import List, Optional

from app.compliance.validators.base import BaseValidator, BuildingContext, ValidatorResult

logger = logging.getLogger(__name__)


# ── Height ────────────────────────────────────────────────────────

class HeightValidator(BaseValidator):
    """
    Maximum building height for G+3 residential: 15 m.

    Rule: BBMP-RES-G001
    Source: BBMP Building Bye-Laws 2003, Clause 4.1.
    """

    def validate(self, context: BuildingContext, rule: dict) -> ValidatorResult:
        expected: float = rule["expected_value"]
        unit: str = rule.get("unit", "m")

        # Only applies to non-high-rise buildings
        if context.storeys > 4:
            return ValidatorResult(
                not_applicable=True,
                expected=expected,
                unit=unit,
                na_reason=(
                    "15 m height limit applies to G+3 buildings only. "
                    f"This building has {context.storeys} storeys — "
                    "see high-rise provisions (BBMP-RES-G004)."
                ),
            )

        if context.height is None:
            return ValidatorResult(
                skipped=True,
                expected=expected,
                unit=unit,
                skip_reason="Building height not available in geometry data.",
            )

        actual = context.height
        passed = actual <= expected
        diff = self._numeric_difference(actual, expected)

        if passed:
            return ValidatorResult(
                passed=True,
                actual=actual,
                expected=expected,
                difference=diff,
                unit=unit,
                message=f"Building height {actual} {unit} is within the maximum {expected} {unit}.",
            )

        return ValidatorResult(
            passed=False,
            actual=actual,
            expected=expected,
            difference=diff,
            unit=unit,
            message=self._format_message(rule["message"], actual, expected),
            recommendation=(
                f"Reduce building height by {abs(diff):.2f} {unit} "
                f"to comply with the {expected} {unit} limit for G+3 residential buildings. "
                "Consider reducing storey heights or removing a floor."
            ),
        )


# ── Storeys ───────────────────────────────────────────────────────

class StoreyValidator(BaseValidator):
    """
    Maximum number of storeys for standard residential: 4 (G+3).

    Rule: BBMP-RES-G002
    Source: BBMP Building Bye-Laws 2003, Clause 4.2.
    """

    def validate(self, context: BuildingContext, rule: dict) -> ValidatorResult:
        expected: int = int(rule["expected_value"])
        unit: str = rule.get("unit", "storeys")

        actual = context.storeys
        if actual == 0:
            return ValidatorResult(
                skipped=True,
                expected=expected,
                unit=unit,
                skip_reason="Storey count is 0; IFC may not have IfcBuildingStorey entities.",
            )

        passed = actual <= expected
        diff = self._numeric_difference(actual, expected)

        if passed:
            return ValidatorResult(
                passed=True,
                actual=actual,
                expected=expected,
                difference=diff,
                unit=unit,
                message=f"Building has {actual} storey(s), within the maximum {expected} for standard residential.",
            )

        return ValidatorResult(
            passed=False,
            actual=actual,
            expected=expected,
            difference=diff,
            unit=unit,
            message=self._format_message(rule["message"], actual, expected),
            recommendation=(
                f"Building exceeds G+3 limit by {int(abs(diff))} storey(s). "
                "To exceed G+3, the building must qualify as high-rise with minimum "
                "12 m road width and additional setback and fire safety provisions."
            ),
        )


# ── Storey Heights ────────────────────────────────────────────────

class StoreyHeightValidator(BaseValidator):
    """
    Minimum floor-to-floor height: 2.75 m per floor.

    Rule: BBMP-RES-G003
    Source: BBMP Building Bye-Laws 2003, Clause 4.3.
    """

    def validate(self, context: BuildingContext, rule: dict) -> ValidatorResult:
        expected: float = rule["expected_value"]
        unit: str = rule.get("unit", "m")

        if not context.storey_heights:
            return ValidatorResult(
                skipped=True,
                expected=expected,
                unit=unit,
                skip_reason="Storey heights not available in geometry data.",
            )

        heights: List[float] = context.storey_heights
        below_min = [h for h in heights if h < expected]
        min_height = min(heights) if heights else None
        all_pass = len(below_min) == 0

        if all_pass:
            return ValidatorResult(
                passed=True,
                actual=min_height,
                expected=expected,
                difference=self._numeric_difference(min_height, expected),
                unit=unit,
                message=(
                    f"All {len(heights)} floor(s) meet the minimum height of {expected} {unit}. "
                    f"Minimum floor height is {min_height:.2f} {unit}."
                ),
            )

        return ValidatorResult(
            passed=False,
            actual=min_height,
            expected=expected,
            difference=self._numeric_difference(min_height, expected),
            unit=unit,
            message=(
                f"{len(below_min)} floor(s) have height below the minimum "
                f"{expected} {unit}. Minimum found: {min_height:.2f} {unit}."
            ),
            recommendation=(
                f"Increase the height of the {len(below_min)} deficient floor(s) "
                f"to at least {expected} {unit} clear height for habitability compliance."
            ),
        )


# ── High-Rise Eligibility ─────────────────────────────────────────

class HighRiseEligibilityValidator(BaseValidator):
    """
    High-rise buildings (>4 storeys) require road width ≥ 12 m.

    Rule: BBMP-RES-G004
    Source: BBMP Building Bye-Laws 2003, Clause 4.4, Table 5.
    """

    def validate(self, context: BuildingContext, rule: dict) -> ValidatorResult:
        expected: float = rule["expected_value"]
        unit: str = rule.get("unit", "m")

        # Only applies if building is high-rise
        if context.storeys <= 4:
            return ValidatorResult(
                not_applicable=True,
                expected=expected,
                unit=unit,
                na_reason=(
                    f"High-rise road requirement only applies to buildings "
                    f"above G+3; this building has {context.storeys} storey(s)."
                ),
            )

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
                    f"Road width {actual} {unit} is sufficient for high-rise "
                    f"construction (minimum {expected} {unit})."
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
                f"A high-rise building on a {actual} {unit} road is not permissible. "
                f"The road must be at least {expected} {unit} wide. "
                "Either select a plot abutting a wider road or reduce building height to G+3."
            ),
        )


# ── FAR / FSI ────────────────────────────────────────────────────

class _FARBaseValidator(BaseValidator):
    """Shared logic for all FAR validators."""

    def _validate_far(
        self,
        context: BuildingContext,
        rule: dict,
        plot_min: Optional[float],
        plot_max: Optional[float],
    ) -> ValidatorResult:
        expected: float = rule["expected_value"]
        unit: str = rule.get("unit", "ratio")

        area = context.plot_area
        if area is None:
            return ValidatorResult(
                skipped=True,
                expected=expected,
                unit=unit,
                skip_reason="plot_area not provided — cannot compute FAR.",
            )

        # Check range applicability
        in_range = True
        if plot_min is not None and area < plot_min:
            in_range = False
        if plot_max is not None and area > plot_max:
            in_range = False

        if not in_range:
            range_str = (
                f"≤ {plot_max} sqm" if plot_min is None
                else f"> {plot_min} sqm" if plot_max is None
                else f"{plot_min}–{plot_max} sqm"
            )
            return ValidatorResult(
                not_applicable=True,
                expected=expected,
                unit=unit,
                na_reason=(
                    f"Rule applies to plots {range_str}; "
                    f"this plot is {area} sqm."
                ),
            )

        if context.far is None:
            if context.gross_floor_area is None:
                return ValidatorResult(
                    skipped=True,
                    expected=expected,
                    unit=unit,
                    skip_reason="gross_floor_area not available in geometry — cannot compute FAR.",
                )
            # Attempt recompute
            context.compute_derived_fields()

        if context.far is None:
            return ValidatorResult(
                skipped=True,
                expected=expected,
                unit=unit,
                skip_reason="FAR could not be computed from available data.",
            )

        actual = context.far
        passed = actual <= expected
        diff = self._numeric_difference(actual, expected)

        if passed:
            return ValidatorResult(
                passed=True,
                actual=actual,
                expected=expected,
                difference=diff,
                unit=unit,
                message=f"FAR {actual} is within the maximum permissible FAR of {expected}.",
            )

        return ValidatorResult(
            passed=False,
            actual=actual,
            expected=expected,
            difference=diff,
            unit=unit,
            message=self._format_message(rule["message"], actual, expected),
            recommendation=(
                f"FAR exceeds the limit by {abs(diff):.4f}. "
                f"Reduce gross floor area by approximately "
                f"{abs(diff) * area:.1f} sqm to comply."
            ),
        )


class FARSmallPlotValidator(_FARBaseValidator):
    """FAR validator for plots ≤ 300 sqm (max FAR: 2.25). Rule: BBMP-RES-F001."""

    def validate(self, context: BuildingContext, rule: dict) -> ValidatorResult:
        return self._validate_far(context, rule, plot_min=None, plot_max=300.0)


class FARMediumPlotValidator(_FARBaseValidator):
    """FAR validator for plots 300–500 sqm (max FAR: 2.0). Rule: BBMP-RES-F002."""

    def validate(self, context: BuildingContext, rule: dict) -> ValidatorResult:
        return self._validate_far(context, rule, plot_min=300.0, plot_max=500.0)


class FARLargePlotValidator(_FARBaseValidator):
    """FAR validator for plots > 500 sqm (max FAR: 1.75). Rule: BBMP-RES-F003."""

    def validate(self, context: BuildingContext, rule: dict) -> ValidatorResult:
        return self._validate_far(context, rule, plot_min=500.0, plot_max=None)


# ── Ground Coverage ───────────────────────────────────────────────

class _GroundCoverageBaseValidator(BaseValidator):
    """Shared logic for all ground coverage validators."""

    def _validate_coverage(
        self,
        context: BuildingContext,
        rule: dict,
        plot_min: Optional[float],
        plot_max: Optional[float],
    ) -> ValidatorResult:
        expected: float = rule["expected_value"]
        unit: str = rule.get("unit", "%")

        area = context.plot_area
        if area is None:
            return ValidatorResult(
                skipped=True,
                expected=expected,
                unit=unit,
                skip_reason="plot_area not provided — cannot compute ground coverage.",
            )

        in_range = True
        if plot_min is not None and area < plot_min:
            in_range = False
        if plot_max is not None and area > plot_max:
            in_range = False

        if not in_range:
            return ValidatorResult(
                not_applicable=True,
                expected=expected,
                unit=unit,
                na_reason=f"This coverage rule does not apply to this plot size ({area} sqm).",
            )

        if context.ground_coverage_pct is None:
            if context.footprint is None:
                return ValidatorResult(
                    skipped=True,
                    expected=expected,
                    unit=unit,
                    skip_reason="Building footprint not available in geometry — cannot compute ground coverage.",
                )
            context.compute_derived_fields()

        if context.ground_coverage_pct is None:
            return ValidatorResult(
                skipped=True,
                expected=expected,
                unit=unit,
                skip_reason="Ground coverage could not be computed from available data.",
            )

        actual = context.ground_coverage_pct
        passed = actual <= expected
        diff = self._numeric_difference(actual, expected)

        if passed:
            return ValidatorResult(
                passed=True,
                actual=actual,
                expected=expected,
                difference=diff,
                unit=unit,
                message=f"Ground coverage {actual}% is within the maximum {expected}%.",
            )

        return ValidatorResult(
            passed=False,
            actual=actual,
            expected=expected,
            difference=diff,
            unit=unit,
            message=self._format_message(rule["message"], actual, expected),
            recommendation=(
                f"Ground coverage exceeds the limit by {abs(diff):.2f}%. "
                f"Reduce the building footprint by approximately "
                f"{(abs(diff) / 100) * area:.1f} sqm to comply."
            ),
        )


class GroundCoverageSmallValidator(_GroundCoverageBaseValidator):
    """Ground coverage for plots ≤ 300 sqm (max 60%). Rule: BBMP-RES-C001."""

    def validate(self, context: BuildingContext, rule: dict) -> ValidatorResult:
        return self._validate_coverage(context, rule, plot_min=None, plot_max=300.0)


class GroundCoverageMediumValidator(_GroundCoverageBaseValidator):
    """Ground coverage for plots 300–500 sqm (max 55%). Rule: BBMP-RES-C002."""

    def validate(self, context: BuildingContext, rule: dict) -> ValidatorResult:
        return self._validate_coverage(context, rule, plot_min=300.0, plot_max=500.0)


class GroundCoverageLargeValidator(_GroundCoverageBaseValidator):
    """Ground coverage for plots > 500 sqm (max 50%). Rule: BBMP-RES-C003."""

    def validate(self, context: BuildingContext, rule: dict) -> ValidatorResult:
        return self._validate_coverage(context, rule, plot_min=500.0, plot_max=None)
