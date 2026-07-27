"""
AI Building Compliance System — Compliance Engine v2 Schemas

Pydantic v2 request/response models for the Municipal Rule Engine.

v2 additions (all backward-compatible — no fields removed):
  - BuildingType enum (8 building types)
  - ClassificationResult (Stage 1 output)
  - Extended BuildingParams (lift, basement, rooms, fire, open space, etc.)
  - ComplianceRequest gains override_building_type
  - RuleResult gains bye_law_reference, page_number, table_reference, priority
  - ComplianceReport gains classification_result, loaded_rule_sets,
    not_applicable_rules

The ComplianceReport is the stable downstream contract consumed by
future AI, GIS, and 3D modules. Add optional fields only — never
remove or rename existing fields.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


# ── Building Type ────────────────────────────────────────────────

class BuildingType(str, Enum):
    """BBMP-recognised building categories."""
    RESIDENTIAL_HOUSE = "residential_house"
    APARTMENT         = "apartment"
    COMMERCIAL        = "commercial"
    INDUSTRIAL        = "industrial"
    INSTITUTIONAL     = "institutional"
    MIXED_USE         = "mixed_use"
    PUBLIC_SEMI_PUBLIC = "public_semi_public"
    UNKNOWN           = "unknown"


# ── Severity ─────────────────────────────────────────────────────

class Severity(str, Enum):
    ERROR   = "error"
    WARNING = "warning"
    INFO    = "info"


# ── Overall Status ────────────────────────────────────────────────

class OverallStatus(str, Enum):
    COMPLIANT                = "COMPLIANT"
    NON_COMPLIANT            = "NON_COMPLIANT"
    CONDITIONALLY_COMPLIANT  = "CONDITIONALLY_COMPLIANT"
    INSUFFICIENT_DATA        = "INSUFFICIENT_DATA"


# ── Rule Result Status ────────────────────────────────────────────

class RuleStatus(str, Enum):
    PASSED          = "PASSED"
    FAILED          = "FAILED"
    WARNING         = "WARNING"
    NOT_APPLICABLE  = "NOT_APPLICABLE"
    SKIPPED         = "SKIPPED"


# ── Classification Result ─────────────────────────────────────────

class ClassificationResult(BaseModel):
    """Output of Stage 1: Building Classification Engine."""

    building_type: BuildingType = Field(
        ...,
        description="Detected or overridden building type.",
    )
    confidence: float = Field(
        ...,
        description="Classification confidence score (0.0 – 1.0).",
        ge=0.0,
        le=1.0,
    )
    classification_method: str = Field(
        ...,
        description="Which strategy produced the result (IFC Metadata / Geometry / Heuristic / Override).",
    )
    detected_features: List[str] = Field(
        default_factory=list,
        description="Key features detected from the IFC parse result.",
    )
    scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Per-building-type heuristic scores (for audit).",
    )
    is_override: bool = Field(
        default=False,
        description="True when classification was manually overridden by the caller.",
    )


# ── Building Parameters (caller-supplied) ─────────────────────────

class BuildingParams(BaseModel):
    """
    Site and building parameters not derivable from the IFC file alone.

    All fields are optional so the engine can operate with partial data.
    Missing fields cause specific rules to be SKIPPED rather than crashing.
    """

    # ── Plot dimensions ──────────────────────────────────────────
    plot_area: Optional[float] = Field(
        None, description="Total plot area (sqm).", ge=0, examples=[250.0]
    )
    plot_width: Optional[float] = Field(
        None, description="Plot width perpendicular to road (m).", ge=0
    )
    plot_depth: Optional[float] = Field(
        None, description="Plot depth parallel to road (m).", ge=0
    )

    # ── Road context ─────────────────────────────────────────────
    road_width: Optional[float] = Field(
        None, description="Width of the abutting road (m).", ge=0
    )
    is_corner_plot: bool = Field(
        default=False, description="Plot abuts two roads."
    )
    second_road_width: Optional[float] = Field(
        None, description="Width of second road for corner plots (m).", ge=0
    )

    # ── Setbacks (m) ─────────────────────────────────────────────
    front_setback: Optional[float] = Field(None, ge=0)
    rear_setback: Optional[float] = Field(None, ge=0)
    left_setback: Optional[float] = Field(None, ge=0)
    right_setback: Optional[float] = Field(None, ge=0)

    # ── Zone and use ─────────────────────────────────────────────
    zone: str = Field(default="residential")
    building_use: str = Field(default="residential")

    # ── Dwelling / occupancy ─────────────────────────────────────
    num_units: Optional[int] = Field(None, ge=0)
    num_bedrooms: Optional[int] = Field(None, ge=0)
    num_kitchens: Optional[int] = Field(None, ge=0)
    num_shops: Optional[int] = Field(None, ge=0)
    num_offices: Optional[int] = Field(None, ge=0)
    occupancy_load: Optional[int] = Field(None, ge=0, description="Max simultaneous occupants.")

    # ── Parking ──────────────────────────────────────────────────
    parking_spaces_provided: Optional[int] = Field(None, ge=0)
    garage_width: Optional[float] = Field(None, ge=0)
    garage_length: Optional[float] = Field(None, ge=0)
    has_ramp: Optional[bool] = Field(None)
    ramp_width: Optional[float] = Field(None, ge=0)

    # ── Vertical circulation ──────────────────────────────────────
    num_staircases: Optional[int] = Field(None, ge=0)
    has_lift: Optional[bool] = Field(None)
    num_lifts: Optional[int] = Field(None, ge=0)
    staircase_width: Optional[float] = Field(None, ge=0)

    # ── Basement ─────────────────────────────────────────────────
    has_basement: Optional[bool] = Field(None)
    basement_area: Optional[float] = Field(None, ge=0)

    # ── Room and space dimensions ─────────────────────────────────
    min_room_height: Optional[float] = Field(None, ge=0, description="Minimum clear height across all habitable rooms (m).")
    min_habitable_room_area: Optional[float] = Field(None, ge=0)

    # ── Open space & environment ──────────────────────────────────
    open_space_area: Optional[float] = Field(None, ge=0, description="Open recreational space area (sqm).")
    tree_plantation_count: Optional[int] = Field(None, ge=0)
    has_rainwater_harvesting: Optional[bool] = Field(None)
    has_solar_water_heater: Optional[bool] = Field(None)
    sewage_treatment_plant: Optional[bool] = Field(None)

    # ── Fire safety ───────────────────────────────────────────────
    has_sprinkler_system: Optional[bool] = Field(None)
    has_fire_noc: Optional[bool] = Field(None)
    has_fire_escape: Optional[bool] = Field(None)
    fire_extinguisher_count: Optional[int] = Field(None, ge=0)

    # ── Electrical ────────────────────────────────────────────────
    electrical_clearance: Optional[float] = Field(None, ge=0)

    # ── Loading / industrial ──────────────────────────────────────
    has_loading_dock: Optional[bool] = Field(None)
    factory_floor_area: Optional[float] = Field(None, ge=0)

    # ── Free-text descriptor (helps classifier) ───────────────────
    building_description: Optional[str] = Field(None)


# ── Compliance Request ────────────────────────────────────────────

class ComplianceRequest(BaseModel):
    """
    Input to the Municipal Rule Engine.

    The engine auto-classifies the building type from the IFC parse result.
    Provide ``override_building_type`` to bypass auto-classification.
    """

    file_id: Optional[str] = Field(
        None,
        description="UUID of a previously parsed IFC file (alternative to inline parse_result).",
    )
    parse_result: Optional[Dict[str, Any]] = Field(
        None,
        description="Inline ParseResult JSON from the IFC parser.",
    )
    building_params: BuildingParams = Field(
        ...,
        description="Site and building parameters not derivable from the IFC file.",
    )
    override_building_type: Optional[BuildingType] = Field(
        None,
        description=(
            "Manually override auto-classification. "
            "If set, classification is skipped and this building type is used directly."
        ),
    )
    # v1 backward-compat: rules_file now auto-determined from building type.
    # If provided, it takes precedence for custom rule sets.
    rules_file: Optional[str] = Field(
        None,
        description=(
            "Custom rules file name (without .json). "
            "If omitted, determined automatically from building type. "
            "(Legacy v1 compatibility field.)"
        ),
    )

    @model_validator(mode="after")
    def validate_input_source(self) -> "ComplianceRequest":
        if self.file_id is None and self.parse_result is None:
            raise ValueError(
                "Either 'file_id' or 'parse_result' must be provided."
            )
        return self


# ── Rule Detail ───────────────────────────────────────────────────

class RuleDetail(BaseModel):
    """Full definition of a single rule from the rule repository."""

    rule_id: str
    title: str
    category: str
    building_types: List[str] = Field(default_factory=list)
    authority: str = Field(default="BBMP")
    bye_law_reference: Optional[str] = None
    page_number: Optional[int] = None
    table_reference: Optional[str] = None
    field: Optional[str] = Field(None, description="Context field evaluated by this rule.")
    operator: str
    expected_value: Any
    unit: str
    severity: Severity
    priority: int = Field(default=1)
    conditions: List[Dict[str, Any]] = Field(default_factory=list)
    required_inputs: List[str] = Field(default_factory=list)
    formula: Optional[str] = None
    error_message: str
    recommendation: Optional[str] = None
    explanation: Optional[str] = None
    is_placeholder: bool = Field(default=False)


# ── Rule Evaluation Result ────────────────────────────────────────

class RuleResult(BaseModel):
    """Result of evaluating a single rule against building data."""

    rule_id: str
    title: str
    category: str
    status: RuleStatus
    severity: Severity
    priority: int = Field(default=1)

    # Traceability
    authority: str = Field(default="BBMP")
    bye_law_reference: Optional[str] = None
    page_number: Optional[int] = None
    table_reference: Optional[str] = None
    is_placeholder: bool = Field(default=False)

    # Evaluation details
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    difference: Optional[float] = None
    unit: Optional[str] = None

    # Human-readable output
    message: Optional[str] = None
    explanation: Optional[str] = None
    recommendation: Optional[str] = None


# ── Category Summary ──────────────────────────────────────────────

class CategoryResult(BaseModel):
    category: str
    status: str
    total_rules: int
    passed: int = 0
    failed: int = 0
    warnings: int = 0
    not_applicable: int = 0
    skipped: int = 0
    rules: List[RuleResult] = Field(default_factory=list)


# ── Compliance Summary ────────────────────────────────────────────

class ComplianceSummary(BaseModel):
    total_rules: int
    passed: int = 0
    failed: int = 0
    warnings: int = 0
    not_applicable: int = 0
    skipped: int = 0
    placeholders: int = 0


# ── Report Metadata ───────────────────────────────────────────────

class ReportMetadata(BaseModel):
    authority: str = Field(default="BBMP")
    bye_laws: str = Field(default="2003")
    building_type: str = Field(default="Unknown")
    rules_file: Optional[str] = None
    engine_version: str = Field(default="2.0.0")
    checked_at: datetime
    file_id: Optional[str] = None


# ── Compliance Report (Primary Output) ───────────────────────────

class ComplianceReport(BaseModel):
    """
    Complete compliance report — the stable downstream contract.

    Future modules (AI, GIS, 3D) consume this without modification.
    Rule: Add optional fields only. Never remove or rename existing fields.
    """

    overall_status: OverallStatus
    compliance_score: int = Field(..., ge=0, le=100)
    summary: ComplianceSummary
    category_results: List[CategoryResult]

    # Stage 1 result — present unless classification was suppressed
    classification_result: Optional[ClassificationResult] = None

    # Which rule sets were loaded (e.g. ["bbmp/apartment"])
    loaded_rule_sets: List[str] = Field(default_factory=list)

    violations: List[RuleResult]
    warnings: List[RuleResult]
    passed_rules: List[RuleResult]
    failed_rules: List[RuleResult]
    not_applicable_rules: List[RuleResult] = Field(default_factory=list)

    metadata: ReportMetadata
    building_params_snapshot: Optional[Dict[str, Any]] = None


# ── Supporting API schemas ────────────────────────────────────────

class BuildingTypeInfo(BaseModel):
    """Describes a supported building type."""
    building_type: BuildingType
    label: str
    description: str
    rule_file: str


class ClassifyRequest(BaseModel):
    """Input for the /classify endpoint (classification only)."""
    parse_result: Dict[str, Any] = Field(
        ..., description="ParseResult JSON from the IFC parser."
    )
    building_params: Optional[BuildingParams] = Field(
        None, description="Optional site params (improve heuristic accuracy)."
    )


class ComplianceErrorResponse(BaseModel):
    detail: str

