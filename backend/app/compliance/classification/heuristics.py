"""
AI Building Compliance System — Heuristic Scoring Tables

Data-driven feature → building type scoring tables.
No hardcoded business logic — only pure score contributions.

Each entry is a (feature_condition, score_delta_per_type) pair.
The classifier sums scores across all entries and normalises.
"""

from __future__ import annotations

from typing import Callable, Dict, List, NamedTuple

from app.compliance.classification.features import BuildingFeatures


class ScoreRule(NamedTuple):
    """A single heuristic scoring rule."""

    description: str
    condition: Callable[[BuildingFeatures], bool]
    scores: Dict[str, float]   # building_type → delta


# ──────────────────────────────────────────────────────────────────
# Scoring table
# Keys: residential_house, apartment, commercial, industrial,
#       institutional, mixed_use, public_semi_public
# ──────────────────────────────────────────────────────────────────

SCORING_RULES: List[ScoreRule] = [

    # ── Storey count ─────────────────────────────────────────────
    ScoreRule(
        "Single storey",
        lambda f: f.storeys == 1,
        {"residential_house": 0.40, "apartment": -0.20, "commercial": 0.05,
         "industrial": 0.15, "institutional": 0.05, "mixed_use": 0.0,
         "public_semi_public": 0.10},
    ),

    ScoreRule(
        "2 storeys (G+1)",
        lambda f: f.storeys == 2,
        {"residential_house": 0.30, "apartment": 0.05, "commercial": 0.10,
         "industrial": 0.10, "institutional": 0.05, "mixed_use": 0.05,
         "public_semi_public": 0.05},
    ),
    ScoreRule(
        "3-4 storeys (G+2/G+3)",
        lambda f: 3 <= f.storeys <= 4,
        {"residential_house": 0.10, "apartment": 0.30, "commercial": 0.15,
         "industrial": 0.05, "institutional": 0.15, "mixed_use": 0.15,
         "public_semi_public": 0.10},
    ),
    ScoreRule(
        "5-8 storeys (high-rise)",
        lambda f: 5 <= f.storeys <= 8,
        {"residential_house": -0.20, "apartment": 0.45, "commercial": 0.25,
         "industrial": -0.10, "institutional": 0.10, "mixed_use": 0.20,
         "public_semi_public": 0.05},
    ),
    ScoreRule(
        "More than 8 storeys (tall building)",
        lambda f: f.storeys > 8,
        {"residential_house": -0.40, "apartment": 0.50, "commercial": 0.30,
         "industrial": -0.20, "institutional": 0.10, "mixed_use": 0.20,
         "public_semi_public": 0.0},
    ),

    # ── Footprint ────────────────────────────────────────────────
    ScoreRule(
        "Small footprint (< 200 sqm)",
        lambda f: f.footprint is not None and f.footprint < 200,
        {"residential_house": 0.30, "apartment": -0.05, "commercial": -0.15,
         "industrial": -0.30, "institutional": -0.10, "mixed_use": -0.05,
         "public_semi_public": -0.05},
    ),
    ScoreRule(
        "Medium footprint (200-500 sqm)",
        lambda f: f.footprint is not None and 200 <= f.footprint <= 500,
        {"residential_house": 0.10, "apartment": 0.25, "commercial": 0.20,
         "industrial": 0.05, "institutional": 0.20, "mixed_use": 0.20,
         "public_semi_public": 0.15},
    ),
    ScoreRule(
        "Large footprint (500-2000 sqm)",
        lambda f: f.footprint is not None and 500 < f.footprint <= 2000,
        {"residential_house": -0.20, "apartment": 0.10, "commercial": 0.30,
         "industrial": 0.25, "institutional": 0.30, "mixed_use": 0.20,
         "public_semi_public": 0.25},
    ),
    ScoreRule(
        "Very large footprint (> 2000 sqm)",
        lambda f: f.footprint is not None and f.footprint > 2000,
        {"residential_house": -0.40, "apartment": 0.0, "commercial": 0.30,
         "industrial": 0.45, "institutional": 0.25, "mixed_use": 0.15,
         "public_semi_public": 0.20},
    ),

    # ── Space count ───────────────────────────────────────────────
    ScoreRule(
        "Very few spaces (1-6)",
        lambda f: 1 <= f.spaces <= 6,
        {"residential_house": 0.30, "apartment": 0.05, "commercial": -0.10,
         "industrial": 0.10, "institutional": -0.10, "mixed_use": -0.05,
         "public_semi_public": -0.05},
    ),

    ScoreRule(
        "Moderate spaces (7-15)",
        lambda f: 7 <= f.spaces <= 15,
        {"residential_house": 0.10, "apartment": 0.25, "commercial": 0.15,
         "industrial": 0.05, "institutional": 0.20, "mixed_use": 0.20,
         "public_semi_public": 0.15},
    ),
    ScoreRule(
        "Many spaces (> 20)",
        lambda f: f.spaces > 20,
        {"residential_house": -0.20, "apartment": 0.15, "commercial": 0.30,
         "industrial": 0.05, "institutional": 0.35, "mixed_use": 0.25,
         "public_semi_public": 0.30},
    ),

    # ── Element-based signals ─────────────────────────────────────
    ScoreRule(
        "Multiple staircases (> 2)",
        lambda f: f.stairs > 2,
        {"residential_house": -0.10, "apartment": 0.30, "commercial": 0.20,
         "industrial": 0.0, "institutional": 0.25, "mixed_use": 0.20,
         "public_semi_public": 0.20},
    ),
    ScoreRule(
        "Many doors (> 30)",
        lambda f: f.doors > 30,
        {"residential_house": -0.10, "apartment": 0.15, "commercial": 0.30,
         "industrial": 0.10, "institutional": 0.25, "mixed_use": 0.25,
         "public_semi_public": 0.20},
    ),
    ScoreRule(
        "Many columns (> 20)",
        lambda f: f.columns > 20,
        {"residential_house": -0.15, "apartment": 0.10, "commercial": 0.25,
         "industrial": 0.25, "institutional": 0.20, "mixed_use": 0.15,
         "public_semi_public": 0.15},
    ),

    # ── Explicit feature signals (from building_params) ───────────
    ScoreRule(
        "Multiple dwelling units declared",
        lambda f: f.num_units is not None and f.num_units >= 4,
        {"residential_house": -0.20, "apartment": 0.50, "commercial": 0.0,
         "industrial": -0.20, "institutional": 0.0, "mixed_use": 0.10,
         "public_semi_public": 0.0},
    ),
    ScoreRule(
        "Bedrooms declared",
        lambda f: f.num_bedrooms is not None and f.num_bedrooms > 0,
        {"residential_house": 0.35, "apartment": 0.20, "commercial": -0.20,
         "industrial": -0.30, "institutional": 0.0, "mixed_use": 0.05,
         "public_semi_public": -0.10},
    ),
    ScoreRule(
        "Shops declared",
        lambda f: f.num_shops is not None and f.num_shops > 0,
        {"residential_house": -0.30, "apartment": -0.05, "commercial": 0.45,
         "industrial": -0.10, "institutional": -0.05, "mixed_use": 0.30,
         "public_semi_public": 0.05},
    ),
    ScoreRule(
        "Office spaces declared",
        lambda f: f.num_offices is not None and f.num_offices > 0,
        {"residential_house": -0.25, "apartment": -0.05, "commercial": 0.40,
         "industrial": -0.05, "institutional": 0.15, "mixed_use": 0.30,
         "public_semi_public": 0.10},
    ),
    ScoreRule(
        "Lift present",
        lambda f: f.has_lift is True,
        {"residential_house": -0.20, "apartment": 0.30, "commercial": 0.20,
         "industrial": 0.05, "institutional": 0.20, "mixed_use": 0.20,
         "public_semi_public": 0.15},
    ),
    ScoreRule(
        "Loading dock present",
        lambda f: f.has_loading_dock is True,
        {"residential_house": -0.40, "apartment": -0.20, "commercial": 0.30,
         "industrial": 0.50, "institutional": -0.10, "mixed_use": 0.10,
         "public_semi_public": -0.05},
    ),
    ScoreRule(
        "Factory floor declared",
        lambda f: f.factory_floor_area is not None and f.factory_floor_area > 0,
        {"residential_house": -0.50, "apartment": -0.40, "commercial": -0.10,
         "industrial": 0.60, "institutional": -0.20, "mixed_use": -0.10,
         "public_semi_public": -0.10},
    ),

    # ── Height ────────────────────────────────────────────────────
    ScoreRule(
        "Low height (≤ 10 m)",
        lambda f: f.height is not None and f.height <= 10,
        {"residential_house": 0.25, "apartment": 0.05, "commercial": 0.05,
         "industrial": 0.10, "institutional": 0.05, "mixed_use": 0.0,
         "public_semi_public": 0.05},
    ),
    ScoreRule(
        "Medium height (10-20 m)",
        lambda f: f.height is not None and 10 < f.height <= 20,
        {"residential_house": 0.0, "apartment": 0.25, "commercial": 0.20,
         "industrial": 0.10, "institutional": 0.15, "mixed_use": 0.15,
         "public_semi_public": 0.10},
    ),
    ScoreRule(
        "Tall building (> 20 m)",
        lambda f: f.height is not None and f.height > 20,
        {"residential_house": -0.30, "apartment": 0.30, "commercial": 0.30,
         "industrial": 0.05, "institutional": 0.10, "mixed_use": 0.20,
         "public_semi_public": 0.05},
    ),
]


# ── Keyword tables for Priority 1 (metadata) ──────────────────────

KEYWORD_MAP: Dict[str, str] = {
    # Residential house
    "house":              "residential_house",
    "villa":              "residential_house",
    "bungalow":           "residential_house",
    "duplex":             "residential_house",
    "independent house":  "residential_house",
    "row house":          "residential_house",
    "individual house":   "residential_house",
    "residential house":  "residential_house",
    "single family":      "residential_house",

    # Apartment
    "apartment":          "apartment",
    "flat":               "apartment",
    "residential flat":   "apartment",
    "multi-dwelling":     "apartment",
    "multidwelling":      "apartment",
    "multi dwelling":     "apartment",
    "housing complex":    "apartment",
    "residential complex": "apartment",
    "apartment complex":  "apartment",
    "residential block":  "apartment",

    # Commercial
    "commercial":         "commercial",
    "office":             "commercial",
    "shop":               "commercial",
    "mall":               "commercial",
    "shopping":           "commercial",
    "showroom":           "commercial",
    "hotel":              "commercial",
    "retail":             "commercial",
    "business":           "commercial",
    "bank":               "commercial",
    "plaza":              "commercial",
    "complex commercial": "commercial",

    # Industrial
    "industrial":         "industrial",
    "factory":            "industrial",
    "warehouse":          "industrial",
    "godown":             "industrial",
    "industry":           "industrial",
    "plant":              "industrial",
    "manufacturing":      "industrial",
    "workshop":           "industrial",
    "production":         "industrial",

    # Institutional
    "school":             "institutional",
    "college":            "institutional",
    "university":         "institutional",
    "hospital":           "institutional",
    "clinic":             "institutional",
    "library":            "institutional",
    "temple":             "institutional",
    "church":             "institutional",
    "mosque":             "institutional",
    "educational":        "institutional",
    "healthcare":         "institutional",
    "medical":            "institutional",

    # Mixed use
    "mixed use":          "mixed_use",
    "mixed-use":          "mixed_use",
    "composite":          "mixed_use",
    "mixed":              "mixed_use",

    # Public / Semi-public
    "community hall":     "public_semi_public",
    "public building":    "public_semi_public",
    "government":         "public_semi_public",
    "municipal":          "public_semi_public",
    "recreation":         "public_semi_public",
    "sports":             "public_semi_public",
    "cultural":           "public_semi_public",
    "auditorium":         "public_semi_public",
    "stadium":            "public_semi_public",
}

# Minimum confidence threshold — below this, return UNKNOWN
CONFIDENCE_THRESHOLD = 0.30
