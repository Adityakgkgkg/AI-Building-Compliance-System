"""
Tests for individual validators.

Covers:
  - PlotAreaValidator: pass, fail, skip (missing data)
  - PlotWidthValidator: pass, fail, skip
  - PlotDepthValidator: pass, fail, skip
  - FrontSetbackSmallRoadValidator: pass, fail, N/A, skip
  - FrontSetbackLargeRoadValidator: pass, fail, N/A
  - RearSetbackStandardValidator: pass, fail, N/A (plot > 300)
  - RearSetbackLargeValidator: pass, fail, N/A (plot ≤ 300)
  - HeightValidator: pass, fail, skip, N/A (high-rise)
  - StoreyValidator: pass, fail, skip (zero storeys)
  - StoreyHeightValidator: all pass, partial fail, skip
  - HighRiseEligibilityValidator: N/A for G+3, pass, fail
  - FARSmallPlotValidator: pass, fail, skip (no floor area), N/A (wrong size)
  - GroundCoverageSmallValidator: pass, fail, skip, N/A
  - RoadWidthValidator: pass, fail, skip
  - ElectricalClearanceValidator: pass, fail, skip
  - ParkingSpacesValidator: pass, fail, skip
  - GarageWidthValidator, GarageLengthValidator
  - FireSprinklerValidator: N/A for G+3, pass, fail
  - RainwaterHarvestingValidator: N/A for small plot, pass, fail
"""

from __future__ import annotations

import pytest

from app.compliance.validators.base import BuildingContext, ValidatorResult
from app.compliance.validators.plot_validators import (
    PlotAreaValidator, PlotWidthValidator, PlotDepthValidator
)
from app.compliance.validators.setback_validators import (
    FrontSetbackSmallRoadValidator,
    FrontSetbackLargeRoadValidator,
    RearSetbackStandardValidator,
    RearSetbackLargeValidator,
    LeftSetbackValidator,
    RightSetbackValidator,
    HighRiseSetbackValidator,
)
from app.compliance.validators.geometry_validators import (
    HeightValidator,
    StoreyValidator,
    StoreyHeightValidator,
    HighRiseEligibilityValidator,
    FARSmallPlotValidator,
    FARMediumPlotValidator,
    FARLargePlotValidator,
    GroundCoverageSmallValidator,
)
from app.compliance.validators.access_validators import (
    RoadWidthValidator,
    ElectricalClearanceValidator,
)
from app.compliance.validators.parking_validators import (
    ParkingSpacesValidator,
    GarageWidthValidator,
    GarageLengthValidator,
    FireSprinklerValidator,
    RainwaterHarvestingValidator,
)


def _rule(rule_id: str, expected_value, unit: str = "m", severity: str = "error") -> dict:
    """Helper to build a minimal rule dict for testing."""
    return {
        "rule_id": rule_id,
        "expected_value": expected_value,
        "unit": unit,
        "severity": severity,
        "message": "Actual {actual} {unit} is below {expected} {unit}.",
    }


def _ctx(**kwargs) -> BuildingContext:
    """Helper to build a BuildingContext with overrides."""
    ctx = BuildingContext(**kwargs)
    ctx.compute_derived_fields()
    return ctx


# ── Plot Validators ───────────────────────────────────────────────

class TestPlotAreaValidator:
    v = PlotAreaValidator()
    rule = _rule("BBMP-RES-P001", expected_value=50.0, unit="sqm")

    def test_pass(self) -> None:
        r = self.v.validate(_ctx(plot_area=100.0), self.rule)
        assert r.passed is True
        assert r.actual == 100.0
        assert r.expected == 50.0
        assert r.difference == 50.0

    def test_fail(self) -> None:
        r = self.v.validate(_ctx(plot_area=30.0), self.rule)
        assert r.passed is False
        assert r.difference == -20.0
        assert r.recommendation is not None

    def test_equal_to_minimum_passes(self) -> None:
        r = self.v.validate(_ctx(plot_area=50.0), self.rule)
        assert r.passed is True

    def test_skip_when_missing(self) -> None:
        r = self.v.validate(_ctx(), self.rule)
        assert r.skipped is True
        assert r.passed is False


class TestPlotWidthValidator:
    v = PlotWidthValidator()
    rule = _rule("BBMP-RES-P002", expected_value=4.5)

    def test_pass(self) -> None:
        r = self.v.validate(_ctx(plot_width=10.0), self.rule)
        assert r.passed is True

    def test_fail(self) -> None:
        r = self.v.validate(_ctx(plot_width=3.0), self.rule)
        assert r.passed is False
        assert r.difference < 0

    def test_skip(self) -> None:
        r = self.v.validate(_ctx(), self.rule)
        assert r.skipped is True


class TestPlotDepthValidator:
    v = PlotDepthValidator()
    rule = _rule("BBMP-RES-P003", expected_value=9.0)

    def test_pass(self) -> None:
        r = self.v.validate(_ctx(plot_depth=12.0), self.rule)
        assert r.passed is True

    def test_fail(self) -> None:
        r = self.v.validate(_ctx(plot_depth=5.0), self.rule)
        assert r.passed is False


# ── Setback Validators ────────────────────────────────────────────

class TestFrontSetbackSmallRoad:
    v = FrontSetbackSmallRoadValidator()
    rule = _rule("BBMP-RES-S001", expected_value=1.5)

    def test_pass_on_small_road(self) -> None:
        r = self.v.validate(_ctx(road_width=9.0, front_setback=2.0), self.rule)
        assert r.passed is True

    def test_fail_on_small_road(self) -> None:
        r = self.v.validate(_ctx(road_width=7.0, front_setback=0.5), self.rule)
        assert r.passed is False

    def test_na_when_large_road(self) -> None:
        r = self.v.validate(_ctx(road_width=12.0, front_setback=0.5), self.rule)
        assert r.not_applicable is True

    def test_na_when_road_below_6m(self) -> None:
        r = self.v.validate(_ctx(road_width=4.0, front_setback=0.5), self.rule)
        assert r.not_applicable is True

    def test_skip_missing_road(self) -> None:
        r = self.v.validate(_ctx(front_setback=2.0), self.rule)
        assert r.skipped is True

    def test_skip_missing_setback(self) -> None:
        r = self.v.validate(_ctx(road_width=7.0), self.rule)
        assert r.skipped is True


class TestFrontSetbackLargeRoad:
    v = FrontSetbackLargeRoadValidator()
    rule = _rule("BBMP-RES-S002", expected_value=3.0)

    def test_pass(self) -> None:
        r = self.v.validate(_ctx(road_width=12.0, front_setback=3.5), self.rule)
        assert r.passed is True

    def test_fail(self) -> None:
        r = self.v.validate(_ctx(road_width=12.0, front_setback=1.0), self.rule)
        assert r.passed is False

    def test_na_on_small_road(self) -> None:
        r = self.v.validate(_ctx(road_width=6.0, front_setback=1.0), self.rule)
        assert r.not_applicable is True


class TestRearSetbackStandard:
    v = RearSetbackStandardValidator()
    rule = _rule("BBMP-RES-S003", expected_value=1.0)

    def test_pass(self) -> None:
        r = self.v.validate(_ctx(plot_area=200.0, rear_setback=1.5), self.rule)
        assert r.passed is True

    def test_fail(self) -> None:
        r = self.v.validate(_ctx(plot_area=200.0, rear_setback=0.5), self.rule)
        assert r.passed is False

    def test_na_for_large_plot(self) -> None:
        r = self.v.validate(_ctx(plot_area=400.0, rear_setback=1.0), self.rule)
        assert r.not_applicable is True


class TestRearSetbackLarge:
    v = RearSetbackLargeValidator()
    rule = _rule("BBMP-RES-S004", expected_value=2.0)

    def test_pass(self) -> None:
        r = self.v.validate(_ctx(plot_area=400.0, rear_setback=2.5), self.rule)
        assert r.passed is True

    def test_fail(self) -> None:
        r = self.v.validate(_ctx(plot_area=400.0, rear_setback=1.0), self.rule)
        assert r.passed is False

    def test_na_for_small_plot(self) -> None:
        r = self.v.validate(_ctx(plot_area=200.0, rear_setback=1.0), self.rule)
        assert r.not_applicable is True


class TestHighRiseSetback:
    v = HighRiseSetbackValidator()
    rule = _rule("BBMP-RES-S007", expected_value=6.0)

    def test_na_for_standard_building(self) -> None:
        r = self.v.validate(
            _ctx(storeys=3, front_setback=1.5, rear_setback=1.0, left_setback=1.0, right_setback=1.0),
            self.rule
        )
        assert r.not_applicable is True

    def test_fail_for_highrise_with_small_setback(self) -> None:
        ctx = _ctx(
            storeys=5,
            front_setback=3.0,  # min will be 3.0 < 6.0
            rear_setback=6.0,
            left_setback=6.0,
            right_setback=6.0,
        )
        r = self.v.validate(ctx, self.rule)
        assert r.passed is False
        assert r.actual == 3.0

    def test_pass_for_highrise(self) -> None:
        ctx = _ctx(
            storeys=5,
            front_setback=7.0,
            rear_setback=7.0,
            left_setback=6.0,
            right_setback=6.0,
        )
        r = self.v.validate(ctx, self.rule)
        assert r.passed is True


# ── Geometry Validators ───────────────────────────────────────────

class TestHeightValidator:
    v = HeightValidator()
    rule = _rule("BBMP-RES-G001", expected_value=15.0)

    def test_pass(self) -> None:
        r = self.v.validate(_ctx(storeys=3, height=10.5), self.rule)
        assert r.passed is True

    def test_fail(self) -> None:
        r = self.v.validate(_ctx(storeys=3, height=17.0), self.rule)
        assert r.passed is False
        assert r.difference > 0

    def test_na_for_highrise(self) -> None:
        r = self.v.validate(_ctx(storeys=5, height=20.0), self.rule)
        assert r.not_applicable is True

    def test_skip_missing_height(self) -> None:
        r = self.v.validate(_ctx(storeys=3), self.rule)
        assert r.skipped is True


class TestStoreyValidator:
    v = StoreyValidator()
    rule = _rule("BBMP-RES-G002", expected_value=4, unit="storeys")

    def test_pass(self) -> None:
        r = self.v.validate(_ctx(storeys=3), self.rule)
        assert r.passed is True

    def test_exactly_4_passes(self) -> None:
        r = self.v.validate(_ctx(storeys=4), self.rule)
        assert r.passed is True

    def test_fail_5_storeys(self) -> None:
        r = self.v.validate(_ctx(storeys=5), self.rule)
        assert r.passed is False

    def test_skip_zero_storeys(self) -> None:
        r = self.v.validate(_ctx(storeys=0), self.rule)
        assert r.skipped is True


class TestStoreyHeightValidator:
    v = StoreyHeightValidator()
    rule = _rule("BBMP-RES-G003", expected_value=2.75, severity="warning")

    def test_all_pass(self) -> None:
        r = self.v.validate(_ctx(storey_heights=[3.5, 3.5, 3.0]), self.rule)
        assert r.passed is True

    def test_one_below_minimum(self) -> None:
        r = self.v.validate(_ctx(storey_heights=[3.5, 2.5, 3.0]), self.rule)
        assert r.passed is False
        assert r.actual == 2.5

    def test_skip_missing_data(self) -> None:
        r = self.v.validate(_ctx(), self.rule)
        assert r.skipped is True


class TestFARSmallPlotValidator:
    v = FARSmallPlotValidator()
    rule = _rule("BBMP-RES-F001", expected_value=2.25, unit="ratio")

    def test_pass(self) -> None:
        # plot=200, gfa=400 → FAR=2.0 < 2.25
        ctx = _ctx(plot_area=200.0, gross_floor_area=400.0)
        r = self.v.validate(ctx, self.rule)
        assert r.passed is True
        assert r.actual == pytest.approx(2.0)

    def test_fail(self) -> None:
        # plot=200, gfa=500 → FAR=2.5 > 2.25
        ctx = _ctx(plot_area=200.0, gross_floor_area=500.0)
        r = self.v.validate(ctx, self.rule)
        assert r.passed is False
        assert r.actual == pytest.approx(2.5)

    def test_na_for_large_plot(self) -> None:
        ctx = _ctx(plot_area=400.0, gross_floor_area=800.0)
        r = self.v.validate(ctx, self.rule)
        assert r.not_applicable is True

    def test_skip_missing_floor_area(self) -> None:
        ctx = _ctx(plot_area=200.0)
        r = self.v.validate(ctx, self.rule)
        assert r.skipped is True


class TestGroundCoverageSmall:
    v = GroundCoverageSmallValidator()
    rule = _rule("BBMP-RES-C001", expected_value=60.0, unit="%")

    def test_pass(self) -> None:
        # plot=200, footprint=100 → 50% < 60%
        ctx = _ctx(plot_area=200.0, footprint=100.0)
        r = self.v.validate(ctx, self.rule)
        assert r.passed is True
        assert r.actual == pytest.approx(50.0)

    def test_fail(self) -> None:
        # plot=200, footprint=140 → 70% > 60%
        ctx = _ctx(plot_area=200.0, footprint=140.0)
        r = self.v.validate(ctx, self.rule)
        assert r.passed is False

    def test_na_for_large_plot(self) -> None:
        ctx = _ctx(plot_area=400.0, footprint=200.0)
        r = self.v.validate(ctx, self.rule)
        assert r.not_applicable is True


# ── Access Validators ─────────────────────────────────────────────

class TestRoadWidthValidator:
    v = RoadWidthValidator()
    rule = _rule("BBMP-RES-R001", expected_value=6.0)

    def test_pass(self) -> None:
        r = self.v.validate(_ctx(road_width=9.0), self.rule)
        assert r.passed is True

    def test_fail(self) -> None:
        r = self.v.validate(_ctx(road_width=4.0), self.rule)
        assert r.passed is False

    def test_skip(self) -> None:
        r = self.v.validate(_ctx(), self.rule)
        assert r.skipped is True


class TestElectricalClearance:
    v = ElectricalClearanceValidator()
    rule = _rule("BBMP-RES-R002", expected_value=1.5, severity="warning")

    def test_pass(self) -> None:
        r = self.v.validate(_ctx(electrical_clearance=2.0), self.rule)
        assert r.passed is True

    def test_fail(self) -> None:
        r = self.v.validate(_ctx(electrical_clearance=1.0), self.rule)
        assert r.passed is False

    def test_skip(self) -> None:
        r = self.v.validate(_ctx(), self.rule)
        assert r.skipped is True


# ── Parking Validators ────────────────────────────────────────────

class TestParkingSpacesValidator:
    v = ParkingSpacesValidator()
    rule = _rule("BBMP-RES-K001", expected_value=1, unit="spaces per unit")

    def test_pass(self) -> None:
        r = self.v.validate(_ctx(num_units=3, parking_spaces_provided=3), self.rule)
        assert r.passed is True

    def test_pass_excess(self) -> None:
        r = self.v.validate(_ctx(num_units=2, parking_spaces_provided=5), self.rule)
        assert r.passed is True

    def test_fail(self) -> None:
        r = self.v.validate(_ctx(num_units=4, parking_spaces_provided=2), self.rule)
        assert r.passed is False
        assert r.expected == 4  # 4 units × 1 = 4 required
        assert r.actual == 2

    def test_skip_missing_units(self) -> None:
        r = self.v.validate(_ctx(parking_spaces_provided=3), self.rule)
        assert r.skipped is True


class TestFireSprinklerValidator:
    v = FireSprinklerValidator()
    rule = _rule("BBMP-RES-X001", expected_value=True, unit="boolean")

    def test_na_standard_building(self) -> None:
        r = self.v.validate(_ctx(storeys=3), self.rule)
        assert r.not_applicable is True

    def test_pass_highrise_with_sprinkler(self) -> None:
        r = self.v.validate(_ctx(storeys=5, has_sprinkler_system=True), self.rule)
        assert r.passed is True

    def test_fail_highrise_without_sprinkler(self) -> None:
        r = self.v.validate(_ctx(storeys=5, has_sprinkler_system=False), self.rule)
        assert r.passed is False


class TestRainwaterHarvesting:
    v = RainwaterHarvestingValidator()
    rule = _rule("BBMP-RES-E001", expected_value=True, unit="boolean", severity="warning")

    def test_na_small_plot(self) -> None:
        r = self.v.validate(_ctx(plot_area=50.0, has_rainwater_harvesting=False), self.rule)
        assert r.not_applicable is True

    def test_pass(self) -> None:
        r = self.v.validate(_ctx(plot_area=200.0, has_rainwater_harvesting=True), self.rule)
        assert r.passed is True

    def test_fail(self) -> None:
        r = self.v.validate(_ctx(plot_area=200.0, has_rainwater_harvesting=False), self.rule)
        assert r.passed is False
