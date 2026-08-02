"""
MCRDSE Sprint 1 – Canonical Evidence Schemas
=============================================
Pydantic v2 strict-typed data model defining the ``EvidenceBundle`` — the
single canonical object consumed by all downstream reporting sprints.

Design rules:
- Zero business logic.  All values originate from upstream modules.
- No ``Any`` types.  Every field has a concrete Python type annotation.
- ``model_config = ConfigDict(strict=True)`` on every model.
- Fields that may be legitimately absent from an upstream module are
  ``Optional[T]`` with an explicit ``None`` default; they are never omitted
  silently.

Upstream module → schema mapping:
    Module 1 (IFC Parser)          → BuildingEvidence
    Module 2 (Classification)      → ClassificationEvidence
    Module 3 (GIS Context Engine)  → GISEvidence
    Module 2 (Compliance Engine)   → ComplianceEvidence, RuleResult
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Shared config ─────────────────────────────────────────────────────────────
_STRICT = ConfigDict(strict=True, frozen=True)


# ─────────────────────────────────────────────────────────────────────────────
# Module 1 — IFC Parser evidence
# ─────────────────────────────────────────────────────────────────────────────

class BuildingEvidence(BaseModel):
    """
    Canonical representation of IFC-parsed building data.

    All fields are populated by the IFC Parser module (Module 1).
    Nothing is calculated here; values are mapped 1-to-1 from parser output.
    """

    model_config = _STRICT

    building_id: str = Field(
        ...,
        description="Unique identifier for the building (derived from IFC GlobalId or UUID).",
    )
    building_name: str = Field(
        ...,
        description="Human-readable building name as extracted from the IFC file.",
    )
    ifc_file: str = Field(
        ...,
        description="Original IFC filename uploaded for this compliance check.",
    )
    building_type: str = Field(
        ...,
        description="IFC building type string (e.g., 'RESIDENTIAL', 'COMMERCIAL').",
    )
    plot_area: float = Field(
        ...,
        ge=0.0,
        description="Total plot/site area in square metres.",
    )
    builtup_area: float = Field(
        ...,
        ge=0.0,
        description="Total built-up area across all floors in square metres.",
    )
    height: float = Field(
        ...,
        ge=0.0,
        description="Overall building height in metres.",
    )
    floors: int = Field(
        ...,
        ge=0,
        description="Total number of floors including ground floor.",
    )
    fsi: float = Field(
        ...,
        ge=0.0,
        description="Floor Space Index (FSI) = built-up area / plot area.",
    )
    ground_coverage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Ground coverage ratio as a percentage of plot area.",
    )
    occupancy: str = Field(
        ...,
        description="Occupancy classification string from the IFC parser.",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Module 2 — Building Classification evidence
# ─────────────────────────────────────────────────────────────────────────────

class ClassificationEvidence(BaseModel):
    """
    Canonical representation of the building classification output.

    Populated by the Building Classification service (Module 2).
    """

    model_config = _STRICT

    predicted_type: str = Field(
        ...,
        description=(
            "Predicted building category "
            "(Residential, Commercial, Apartment, Industrial, Mixed Use)."
        ),
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Classifier confidence score in [0.0, 1.0].",
    )
    reason: str = Field(
        ...,
        description="Human-readable explanation of why this classification was assigned.",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Module 3 — GIS Context Engine evidence
# ─────────────────────────────────────────────────────────────────────────────

class DatasetProvenance(BaseModel):
    """
    Auditable citation for a single GIS dataset used during spatial analysis.
    Maps directly from ``CitationSchema`` in ``app.gis.schemas``.
    """

    model_config = _STRICT

    dataset_name: str = Field(..., description="Official dataset name.")
    authority: str = Field(..., description="Governing authority that owns the dataset.")
    source_url: str = Field(..., description="Canonical URL of the dataset source.")
    license: str = Field(..., description="Data license identifier.")
    feature_id: Optional[str] = Field(
        default=None,
        description="Specific feature ID matched during spatial lookup (if applicable).",
    )
    observation: str = Field(
        ...,
        description="Human-readable observation recorded during this spatial lookup.",
    )


class GISEvidence(BaseModel):
    """
    Canonical representation of the urban spatial context output.

    All fields are projected 1-to-1 from ``GISContextResponse``
    (``app.gis.schemas``).  No spatial calculation is performed here.
    """

    model_config = _STRICT

    authority: str = Field(
        ...,
        description="Planning authority jurisdiction (e.g., 'BBMP').",
    )
    ward: str = Field(
        ...,
        description="BBMP ward name containing the building site.",
    )
    ward_number: Optional[int] = Field(
        default=None,
        description="Numeric ward identifier (if available).",
    )
    zone: str = Field(
        ...,
        description="BBMP administrative zone (e.g., 'South Zone').",
    )
    road_name: str = Field(
        ...,
        description="Name of the nearest public road.",
    )
    road_width: float = Field(
        ...,
        ge=0.0,
        description="Effective road width in metres.",
    )
    land_use: str = Field(
        ...,
        description="BDA Master Plan land-use classification for the site.",
    )
    lake_distance: float = Field(
        ...,
        ge=0.0,
        description="Distance to the nearest water body / lake boundary in metres.",
    )
    lake_buffer: bool = Field(
        ...,
        description="True if site is within 30 m or 75 m regulated lake buffer zone.",
    )
    airport_zone: bool = Field(
        ...,
        description="True if site lies within an airport height restriction funnel.",
    )
    airport_height_limit: Optional[float] = Field(
        default=None,
        description="Maximum permitted building height in metres AGL/AMSL (if restricted).",
    )
    flood_risk: str = Field(
        ...,
        description="Municipal flood risk classification: 'Low', 'Medium', or 'High'.",
    )
    heritage_zone: bool = Field(
        ...,
        description="True if site is within a designated heritage conservation zone.",
    )
    dataset_manifest: List[DatasetProvenance] = Field(
        default_factory=list,
        description="Ordered list of GIS datasets consulted during spatial analysis.",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Module 2 — Compliance Engine evidence
# ─────────────────────────────────────────────────────────────────────────────

class RuleResult(BaseModel):
    """
    Per-rule evaluation record produced by the Compliance Engine.

    Each instance represents a single evaluated building regulation.
    All values originate from the rule engine — nothing is re-derived here.
    """

    model_config = _STRICT

    rule_id: str = Field(
        ...,
        description="Unique machine-readable rule identifier (e.g., 'BBMP-FSI-001').",
    )
    rule_name: str = Field(
        ...,
        description="Human-readable rule name.",
    )
    status: str = Field(
        ...,
        description="Evaluation outcome: 'PASSED', 'FAILED', or 'WARNING'.",
    )
    severity: str = Field(
        ...,
        description="Rule severity: 'BLOCKING', 'MAJOR', 'MINOR', or 'INFO'.",
    )
    expected: str = Field(
        ...,
        description="The permitted/required value as defined by the regulation.",
    )
    actual: str = Field(
        ...,
        description="The measured/calculated value from the building data.",
    )
    difference: str = Field(
        ...,
        description="Deviation between actual and expected (formatted string with units).",
    )
    message: str = Field(
        ...,
        description="Plain-language compliance verdict message.",
    )
    clause: str = Field(
        ...,
        description="Regulatory clause reference (e.g., 'BBMP Bye-law 7.3.2').",
    )
    reference: str = Field(
        ...,
        description="Source document title and section (e.g., 'BBMP Building Bye-laws 2024, §7').",
    )
    recommendation: str = Field(
        ...,
        description="Corrective action recommended when rule is not passed.",
    )


class ComplianceEvidence(BaseModel):
    """
    Canonical representation of all compliance engine results.

    Aggregates ``RuleResult`` records produced by the Compliance Engine
    (Module 2).  Score and rule counts are taken directly from engine output —
    not recomputed.
    """

    model_config = _STRICT

    rules_checked: int = Field(
        ...,
        ge=0,
        description="Total number of applicable rules evaluated.",
    )
    passed: int = Field(
        ...,
        ge=0,
        description="Number of rules that passed.",
    )
    failed: int = Field(
        ...,
        ge=0,
        description="Number of rules that failed.",
    )
    warnings: int = Field(
        ...,
        ge=0,
        description="Number of rules that produced warnings.",
    )
    blocking: int = Field(
        ...,
        ge=0,
        description="Number of BLOCKING violations that prevent approval.",
    )
    score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Overall compliance score in [0.0, 100.0] as reported by the engine.",
    )
    rule_results: List[RuleResult] = Field(
        default_factory=list,
        description="Full per-rule evaluation records from the compliance engine.",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Collection metadata
# ─────────────────────────────────────────────────────────────────────────────

class CollectionMetadata(BaseModel):
    """
    Provenance and timing metadata for the evidence collection run.

    Records which module versions produced the data and how long each
    collection step took, to support audit and performance monitoring.
    """

    model_config = _STRICT

    collected_at: datetime = Field(
        ...,
        description="UTC datetime when bundle assembly completed.",
    )
    building_collection_ms: float = Field(
        ...,
        ge=0.0,
        description="Wall-clock time taken to collect IFC Parser evidence (ms).",
    )
    classification_collection_ms: float = Field(
        ...,
        ge=0.0,
        description="Wall-clock time taken to collect Classification evidence (ms).",
    )
    gis_collection_ms: float = Field(
        ...,
        ge=0.0,
        description="Wall-clock time taken to collect GIS Context evidence (ms).",
    )
    compliance_collection_ms: float = Field(
        ...,
        ge=0.0,
        description="Wall-clock time taken to collect Compliance Engine evidence (ms).",
    )
    total_collection_ms: float = Field(
        ...,
        ge=0.0,
        description="Total end-to-end wall-clock time for bundle assembly (ms).",
    )
    ifc_parser_version: str = Field(
        ...,
        description="Semantic version string of the IFC Parser module.",
    )
    classification_version: str = Field(
        ...,
        description="Semantic version string of the Building Classification module.",
    )
    gis_engine_version: str = Field(
        ...,
        description="Semantic version string of the GIS Context Engine module.",
    )
    compliance_engine_version: str = Field(
        ...,
        description="Semantic version string of the Compliance Engine module.",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Root canonical object
# ─────────────────────────────────────────────────────────────────────────────

class EvidenceBundle(BaseModel):
    """
    Canonical root object for Module 4 Municipal Compliance Reporting.

    This is the **single source of truth** consumed by all downstream
    reporting, PDF generation, AI recommendation, and dashboard sprints.

    Assembly rules:
    - ``report_id`` is a UUID4 generated once per collection run.
    - ``timestamp`` is the UTC instant bundle assembly began.
    - Sub-objects (building, classification, gis, compliance) are collected
      by ``EvidenceCollector`` from live upstream module outputs.
    - ``metadata`` records timing and module version provenance.
    - ``software_version`` is the application version from settings.

    No field may be defaulted to a hardcoded business value.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    report_id: str = Field(
        ...,
        description="UUID4 unique identifier for this evidence collection run.",
    )
    timestamp: datetime = Field(
        ...,
        description="UTC datetime when evidence bundle collection was initiated.",
    )
    building: BuildingEvidence = Field(
        ...,
        description="IFC-parsed building metadata from Module 1.",
    )
    classification: ClassificationEvidence = Field(
        ...,
        description="Building type classification from Module 2.",
    )
    gis: GISEvidence = Field(
        ...,
        description="Urban spatial context from Module 3 GIS Context Engine.",
    )
    compliance: ComplianceEvidence = Field(
        ...,
        description="Rule evaluation results from Module 2 Compliance Engine.",
    )
    metadata: CollectionMetadata = Field(
        ...,
        description="Evidence collection timing and module provenance metadata.",
    )
    software_version: str = Field(
        ...,
        description="Application software version at the time of this report.",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Structured error envelope (returned when an upstream module is unavailable)
# ─────────────────────────────────────────────────────────────────────────────

class ModuleErrorDetail(BaseModel):
    """
    Machine-readable structured error envelope for a failed module collection.

    Returned inside the HTTP response body so clients can distinguish which
    upstream module failed, rather than receiving a generic 500.
    """

    model_config = _STRICT

    error_code: str = Field(
        ...,
        description="Machine-readable error code from the exception hierarchy.",
    )
    module: str = Field(
        ...,
        description="Name of the upstream module that could not be reached.",
    )
    detail: str = Field(
        ...,
        description="Human-readable description of why the module is unavailable.",
    )
