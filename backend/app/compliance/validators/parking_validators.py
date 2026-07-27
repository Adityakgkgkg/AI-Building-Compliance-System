"""
AI Building Compliance System — Parking Validators

Validators for parking and garage checks:
  - ParkingSpacesValidator   (BBMP-RES-K001)
  - GarageWidthValidator     (BBMP-RES-K002)
  - GarageLengthValidator    (BBMP-RES-K003)

Placeholder validators:
  - FireSprinklerValidator   (BBMP-RES-X001)
  - FireEscapeValidator      (BBMP-RES-X002)
  - RainwaterHarvestingValidator (BBMP-RES-E001)
  - SolarWaterHeaterValidator    (BBMP-RES-E002)
"""

from __future__ import annotations

import logging

from app.compliance.validators.base import BaseValidator, BuildingContext, ValidatorResult

logger = logging.getLogger(__name__)


# ── Parking Spaces ────────────────────────────────────────────────

class ParkingSpacesValidator(BaseValidator):
    """
    Minimum parking spaces: 1 per dwelling unit.

    Rule: BBMP-RES-K001
    Source: BBMP Building Bye-Laws 2003, Clause 9.1, Annexure A.
    """

    def validate(self, context: BuildingContext, rule: dict) -> ValidatorResult:
        expected_per_unit: int = int(rule["expected_value"])
        unit: str = rule.get("unit", "spaces per unit")

        if context.num_units is None:
            return ValidatorResult(
                skipped=True,
                expected=expected_per_unit,
                unit=unit,
                skip_reason="num_units not provided in building_params.",
            )

        if context.parking_spaces_provided is None:
            return ValidatorResult(
                skipped=True,
                expected=expected_per_unit,
                unit=unit,
                skip_reason="parking_spaces_provided not provided in building_params.",
            )

        required = context.num_units * expected_per_unit
        actual = context.parking_spaces_provided
        passed = actual >= required
        diff = self._numeric_difference(actual, required)

        if passed:
            return ValidatorResult(
                passed=True,
                actual=actual,
                expected=required,
                difference=diff,
                unit="spaces",
                message=(
                    f"{actual} parking space(s) provided for {context.num_units} unit(s); "
                    f"minimum required is {required} space(s)."
                ),
            )

        return ValidatorResult(
            passed=False,
            actual=actual,
            expected=required,
            difference=diff,
            unit="spaces",
            message=self._format_message(
                rule["message"], actual, expected_per_unit, units=context.num_units
            ),
            recommendation=(
                f"{int(abs(diff))} additional parking space(s) required. "
                f"Provide {required} total parking spaces for {context.num_units} unit(s)."
            ),
        )


# ── Garage / Stall Dimensions ─────────────────────────────────────

class GarageWidthValidator(BaseValidator):
    """
    Minimum parking stall width: 2.5 m.

    Rule: BBMP-RES-K002
    Source: BBMP Building Bye-Laws 2003, Clause 9.2, Annexure A.
    """

    def validate(self, context: BuildingContext, rule: dict) -> ValidatorResult:
        expected: float = rule["expected_value"]
        unit: str = rule.get("unit", "m")

        if context.garage_width is None:
            return ValidatorResult(
                skipped=True,
                expected=expected,
                unit=unit,
                skip_reason="garage_width not provided in building_params.",
            )

        actual = context.garage_width
        passed = actual >= expected
        diff = self._numeric_difference(actual, expected)

        if passed:
            return ValidatorResult(
                passed=True,
                actual=actual,
                expected=expected,
                difference=diff,
                unit=unit,
                message=f"Parking stall width {actual} {unit} meets minimum {expected} {unit}.",
            )

        return ValidatorResult(
            passed=False,
            actual=actual,
            expected=expected,
            difference=diff,
            unit=unit,
            message=self._format_message(rule["message"], actual, expected),
            recommendation=(
                f"Increase parking stall width by {abs(diff):.2f} {unit} "
                f"to meet the BBMP minimum of {expected} {unit}."
            ),
        )


class GarageLengthValidator(BaseValidator):
    """
    Minimum parking stall length: 5.0 m.

    Rule: BBMP-RES-K003
    Source: BBMP Building Bye-Laws 2003, Clause 9.2, Annexure A.
    """

    def validate(self, context: BuildingContext, rule: dict) -> ValidatorResult:
        expected: float = rule["expected_value"]
        unit: str = rule.get("unit", "m")

        if context.garage_length is None:
            return ValidatorResult(
                skipped=True,
                expected=expected,
                unit=unit,
                skip_reason="garage_length not provided in building_params.",
            )

        actual = context.garage_length
        passed = actual >= expected
        diff = self._numeric_difference(actual, expected)

        if passed:
            return ValidatorResult(
                passed=True,
                actual=actual,
                expected=expected,
                difference=diff,
                unit=unit,
                message=f"Parking stall length {actual} {unit} meets minimum {expected} {unit}.",
            )

        return ValidatorResult(
            passed=False,
            actual=actual,
            expected=expected,
            difference=diff,
            unit=unit,
            message=self._format_message(rule["message"], actual, expected),
            recommendation=(
                f"Increase parking stall length by {abs(diff):.2f} {unit} "
                f"to meet the BBMP minimum of {expected} {unit}."
            ),
        )


# ── Fire Safety Placeholders ──────────────────────────────────────

class FireSprinklerValidator(BaseValidator):
    """
    Placeholder: Automatic sprinkler system for high-rise.

    Rule: BBMP-RES-X001 (placeholder — requires fire NOC review).
    Source: BBMP Building Bye-Laws 2003, Clause 10.1; NBC 2016 Part 4.
    """

    def validate(self, context: BuildingContext, rule: dict) -> ValidatorResult:
        unit: str = rule.get("unit", "boolean")

        if context.storeys <= 4:
            return ValidatorResult(
                not_applicable=True,
                expected=True,
                unit=unit,
                na_reason=(
                    f"Sprinkler system rule applies to high-rise buildings (>G+3). "
                    f"This building has {context.storeys} storey(s)."
                ),
            )

        if context.has_sprinkler_system is None:
            return ValidatorResult(
                skipped=True,
                expected=True,
                unit=unit,
                skip_reason=(
                    "has_sprinkler_system not provided. "
                    "Provide fire safety details or obtain fire NOC."
                ),
            )

        actual = context.has_sprinkler_system
        passed = actual is True

        if passed:
            return ValidatorResult(
                passed=True,
                actual=actual,
                expected=True,
                unit=unit,
                message="Automatic sprinkler system is installed.",
            )

        return ValidatorResult(
            passed=False,
            actual=actual,
            expected=True,
            unit=unit,
            message=rule["message"],
            recommendation=(
                "Install an NBC Part 4 compliant automatic sprinkler system. "
                "Obtain fire NOC from Karnataka Fire and Emergency Services."
            ),
        )


class FireEscapeValidator(BaseValidator):
    """
    Placeholder: Minimum 2 staircases for buildings > G+2.

    Rule: BBMP-RES-X002 (placeholder — staircase geometry from IFC is approximate).
    Source: BBMP Building Bye-Laws 2003, Clause 10.2; NBC 2016 Part 4.
    """

    def validate(self, context: BuildingContext, rule: dict) -> ValidatorResult:
        expected: int = int(rule["expected_value"])
        unit: str = rule.get("unit", "staircases")

        if context.storeys <= 3:
            return ValidatorResult(
                not_applicable=True,
                expected=expected,
                unit=unit,
                na_reason=(
                    f"Fire escape staircase rule applies to buildings > G+2. "
                    f"This building has {context.storeys} storey(s)."
                ),
            )

        actual = context.stairs
        passed = actual >= expected
        diff = self._numeric_difference(actual, expected)

        if passed:
            return ValidatorResult(
                passed=True,
                actual=actual,
                expected=expected,
                difference=diff,
                unit=unit,
                message=f"{actual} staircase(s) found; minimum {expected} required.",
            )

        return ValidatorResult(
            passed=False,
            actual=actual,
            expected=expected,
            difference=diff,
            unit=unit,
            message=self._format_message(rule["message"], actual, expected),
            recommendation=(
                f"Provide at least {expected} independent staircase enclosures "
                "as fire escape routes per NBC 2016 Part 4."
            ),
        )


# ── Environmental Placeholders ────────────────────────────────────

class RainwaterHarvestingValidator(BaseValidator):
    """
    Placeholder: Rainwater harvesting for plots ≥ 100 sqm.

    Rule: BBMP-RES-E001 (placeholder).
    Source: BBMP Building Bye-Laws 2003, Clause 11.1.
    """

    def validate(self, context: BuildingContext, rule: dict) -> ValidatorResult:
        unit: str = rule.get("unit", "boolean")
        area = context.plot_area

        if area is not None and area < 100.0:
            return ValidatorResult(
                not_applicable=True,
                expected=True,
                unit=unit,
                na_reason=(
                    f"Rainwater harvesting is mandatory for plots ≥ 100 sqm; "
                    f"this plot is {area} sqm."
                ),
            )

        if context.has_rainwater_harvesting is None:
            return ValidatorResult(
                skipped=True,
                expected=True,
                unit=unit,
                skip_reason="has_rainwater_harvesting not provided in building_params.",
            )

        actual = context.has_rainwater_harvesting
        passed = actual is True

        if passed:
            return ValidatorResult(
                passed=True,
                actual=actual,
                expected=True,
                unit=unit,
                message="Rainwater harvesting system is installed.",
            )

        return ValidatorResult(
            passed=False,
            actual=actual,
            expected=True,
            unit=unit,
            message=rule["message"],
            recommendation=(
                "Install a rainwater harvesting system as per BBMP guidelines. "
                "Provide pit size and percolation specifications in the building plan."
            ),
        )


class SolarWaterHeaterValidator(BaseValidator):
    """
    Placeholder: Solar water heater for plots ≥ 60 sqm.

    Rule: BBMP-RES-E002 (placeholder).
    Source: BBMP Building Bye-Laws 2003, Clause 11.2; BESCOM Solar Policy.
    """

    def validate(self, context: BuildingContext, rule: dict) -> ValidatorResult:
        unit: str = rule.get("unit", "boolean")
        area = context.plot_area

        if area is not None and area < 60.0:
            return ValidatorResult(
                not_applicable=True,
                expected=True,
                unit=unit,
                na_reason=(
                    f"Solar water heater provision applies to plots ≥ 60 sqm; "
                    f"this plot is {area} sqm."
                ),
            )

        if context.has_solar_water_heater is None:
            return ValidatorResult(
                skipped=True,
                expected=True,
                unit=unit,
                skip_reason="has_solar_water_heater not provided in building_params.",
            )

        actual = context.has_solar_water_heater
        passed = actual is True

        if passed:
            return ValidatorResult(
                passed=True,
                actual=actual,
                expected=True,
                unit=unit,
                message="Solar water heater provision is in place.",
            )

        return ValidatorResult(
            passed=False,
            actual=actual,
            expected=True,
            unit=unit,
            message=rule["message"],
            recommendation=(
                "Incorporate a solar water heater in the building design. "
                "Size the system per BESCOM guidelines (typically 100 LPD per unit)."
            ),
        )
