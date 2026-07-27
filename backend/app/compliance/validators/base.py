"""
AI Building Compliance System — Validator Base

Defines the ValidatorResult dataclass and the abstract BaseValidator
that all concrete validators must implement.

Design:
  - ValidatorResult is a lightweight value-object; it carries everything
    the report generator needs to build RuleResult instances.
  - BaseValidator.validate() receives the full BuildingContext so
    validators can cross-reference any field without tight coupling.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


# ── Validator Result ──────────────────────────────────────────────

@dataclass
class ValidatorResult:
    """
    Outcome of evaluating a single rule against building data.

    Attributes:
        passed:         True if the rule is satisfied.
        actual:         Observed value from the building data.
        expected:       Required value from the rule definition.
        difference:     actual - expected (negative means deficient).
        unit:           Measurement unit string.
        message:        Human-readable result description.
        recommendation: Corrective action (populated when not passed).
        skipped:        True when required data is unavailable.
        skip_reason:    Explanation of why the rule was skipped.
        not_applicable: True when the rule does not apply to this building.
        na_reason:      Explanation of why the rule is not applicable.
    """

    passed: bool = False
    actual: Optional[Any] = None
    expected: Optional[Any] = None
    difference: Optional[float] = None
    unit: Optional[str] = None
    message: Optional[str] = None
    recommendation: Optional[str] = None
    skipped: bool = False
    skip_reason: Optional[str] = None
    not_applicable: bool = False
    na_reason: Optional[str] = None


# ── Building Context ──────────────────────────────────────────────

@dataclass
class BuildingContext:
    """
    Unified view of all building data passed to validators.

    Merges the ParseResult sections with caller-supplied building_params
    so validators never need to know where a value came from.

    All fields are Optional to handle missing IFC data gracefully.
    """

    # From ParseResult.building (BuildingInfo)
    project_name: Optional[str] = None
    building_name: Optional[str] = None
    storeys: int = 0
    ifc_schema: Optional[str] = None
    units: Optional[str] = None

    # From ParseResult.elements (ElementCounts)
    walls: int = 0
    doors: int = 0
    windows: int = 0
    slabs: int = 0
    columns: int = 0
    beams: int = 0
    roofs: int = 0
    stairs: int = 0
    spaces: int = 0
    openings: int = 0

    # From ParseResult.geometry (GeometryInfo)
    gross_floor_area: Optional[float] = None
    height: Optional[float] = None
    storey_heights: Optional[list] = field(default=None)
    footprint: Optional[float] = None
    bounding_box: Optional[dict] = field(default=None)

    # From BuildingParams (caller-supplied site context)
    plot_area: Optional[float] = None
    plot_width: Optional[float] = None
    plot_depth: Optional[float] = None
    road_width: Optional[float] = None
    front_setback: Optional[float] = None
    rear_setback: Optional[float] = None
    left_setback: Optional[float] = None
    right_setback: Optional[float] = None
    zone: str = "residential"
    building_use: str = "residential"
    is_corner_plot: bool = False
    num_units: Optional[int] = None
    parking_spaces_provided: Optional[int] = None
    garage_width: Optional[float] = None
    garage_length: Optional[float] = None
    electrical_clearance: Optional[float] = None
    has_sprinkler_system: Optional[bool] = None
    has_rainwater_harvesting: Optional[bool] = None
    has_solar_water_heater: Optional[bool] = None

    # Computed fields (derived, not from raw data)
    far: Optional[float] = field(default=None)
    ground_coverage_pct: Optional[float] = field(default=None)
    min_setback_all_sides: Optional[float] = field(default=None)

    def compute_derived_fields(self) -> None:
        """
        Compute FAR, ground coverage %, and minimum setback.

        Called once after context is assembled. Derived values are
        used by FAR, coverage, and high-rise setback validators.
        """
        # FAR = gross_floor_area / plot_area
        if self.gross_floor_area and self.plot_area and self.plot_area > 0:
            self.far = round(self.gross_floor_area / self.plot_area, 4)

        # Ground coverage % = (footprint / plot_area) * 100
        if self.footprint and self.plot_area and self.plot_area > 0:
            self.ground_coverage_pct = round(
                (self.footprint / self.plot_area) * 100, 2
            )

        # Minimum setback from all sides (used for high-rise check)
        setbacks = [
            s for s in [
                self.front_setback,
                self.rear_setback,
                self.left_setback,
                self.right_setback,
            ]
            if s is not None
        ]
        if setbacks:
            self.min_setback_all_sides = min(setbacks)


# ── Abstract Base Validator ───────────────────────────────────────

class BaseValidator(ABC):
    """
    Abstract base class for all building compliance validators.

    Each concrete validator handles exactly one type of check
    (e.g. PlotAreaValidator, FARValidator). It receives a fully
    assembled BuildingContext and the rule definition dict, and
    returns a ValidatorResult.

    Subclasses MUST implement validate(). They MAY override
    _format_message() to customize the result message.
    """

    @abstractmethod
    def validate(
        self,
        context: BuildingContext,
        rule: dict,
    ) -> ValidatorResult:
        """
        Evaluate the rule against the building context.

        Args:
            context: Merged building data (geometry + elements + params).
            rule:    Rule definition dict from the JSON rules file.

        Returns:
            ValidatorResult with outcome, actual/expected values, and
            a human-readable message.
        """

    def _format_message(
        self,
        template: str,
        actual: Any,
        expected: Any,
        **kwargs: Any,
    ) -> str:
        """
        Fill the rule message template with actual/expected values.

        Template placeholders: {actual}, {expected}, plus any extras.
        Falls back to the raw template if formatting fails.
        """
        try:
            return template.format(
                actual=actual,
                expected=expected,
                **kwargs,
            )
        except (KeyError, ValueError):
            return template

    def _numeric_difference(
        self,
        actual: Any,
        expected: Any,
    ) -> Optional[float]:
        """Return actual - expected if both are numeric, else None."""
        try:
            return round(float(actual) - float(expected), 4)
        except (TypeError, ValueError):
            return None
