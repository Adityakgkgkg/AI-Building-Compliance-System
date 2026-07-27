"""
AI Building Compliance System — Building Classifier

Stage 1 of the Municipal Rule Engine pipeline.

Classification priority order:
  1. IFC Metadata / caller-supplied override (highest confidence)
  2. Keyword matching on project_name, building_name, description
  3. Heuristic feature scoring

Returns a ClassificationResult with confidence score and audit trail.
If confidence < CONFIDENCE_THRESHOLD, returns UNKNOWN.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.compliance.classification.features import BuildingFeatures, extract_features
from app.compliance.classification.heuristics import (
    CONFIDENCE_THRESHOLD,
    KEYWORD_MAP,
    SCORING_RULES,
)
from app.compliance.schemas import BuildingType, ClassificationResult

logger = logging.getLogger(__name__)

# Supported building types for heuristic scoring
_SCORED_TYPES: List[str] = [
    "residential_house",
    "apartment",
    "commercial",
    "industrial",
    "institutional",
    "mixed_use",
    "public_semi_public",
]


class BuildingClassifier:
    """
    Classifies a building into one of the BBMP building categories
    using a 3-priority strategy.

    Thread-safe (stateless per call).
    """

    def classify(
        self,
        parse_data: Dict[str, Any],
        building_params: Optional[Any] = None,
        override: Optional[BuildingType] = None,
    ) -> ClassificationResult:
        """
        Classify a building from its ParseResult data.

        Args:
            parse_data:      Raw ParseResult dict from the IFC parser.
            building_params: Optional BuildingParams for additional signals.
            override:        If provided, bypass all classification logic.

        Returns:
            ClassificationResult with building_type, confidence, and audit trail.
        """

        # ── Override path ─────────────────────────────────────────
        if override is not None and override != BuildingType.UNKNOWN:
            logger.info("Classification overridden by caller: %s", override.value)
            return ClassificationResult(
                building_type=override,
                confidence=1.0,
                classification_method="Override",
                detected_features=[f"override={override.value}"],
                scores={override.value: 1.0},
                is_override=True,
            )

        # ── Extract features ──────────────────────────────────────
        features = extract_features(parse_data, building_params)
        detected: List[str] = self._summarise_features(features)

        # ── Priority 1: Keyword matching on metadata ──────────────
        metadata_result = self._classify_by_metadata(features)
        if metadata_result is not None:
            btype, matched_keyword = metadata_result
            logger.info(
                "Classified by metadata keyword '%s' → %s",
                matched_keyword,
                btype,
            )
            return ClassificationResult(
                building_type=BuildingType(btype),
                confidence=0.95,
                classification_method="IFC Metadata",
                detected_features=[f"keyword={matched_keyword!r}"] + detected,
                scores={btype: 0.95},
                is_override=False,
            )

        # ── Priority 2 + 3: Geometry + Heuristic scoring ─────────
        scores = self._compute_scores(features)
        if not scores:
            logger.warning("No heuristic scores — returning UNKNOWN.")
            return self._unknown(detected)

        # Require at least one positive score contribution, or confidence >= 0.30
        positive_scores = {k: v for k, v in scores.items() if v > 0}
        if not positive_scores:
            logger.info("No positive heuristic scores — returning UNKNOWN.")
            return self._unknown(detected, scores=scores)

        best_type = max(scores, key=lambda k: scores[k])
        max_score = scores[best_type]
        total = sum(max(0.0, v) for v in scores.values())
        confidence = (max_score / total) if total > 0 else 0.0



        logger.info(
            "Heuristic classification: %s (confidence=%.2f)",
            best_type,
            confidence,
        )

        if confidence < CONFIDENCE_THRESHOLD:
            logger.info(
                "Confidence %.2f < threshold %.2f — returning UNKNOWN.",
                confidence,
                CONFIDENCE_THRESHOLD,
            )
            return self._unknown(detected, scores=scores)

        method = self._determine_method(features)

        return ClassificationResult(
            building_type=BuildingType(best_type),
            confidence=round(confidence, 3),
            classification_method=method,
            detected_features=detected,
            scores={k: round(v, 4) for k, v in scores.items()},
            is_override=False,
        )

    # ── Private helpers ───────────────────────────────────────────

    @staticmethod
    def _classify_by_metadata(
        features: BuildingFeatures,
    ) -> Optional[tuple[str, str]]:
        """
        Try to classify using keyword matching on all metadata text.

        Returns (building_type_str, matched_keyword) or None.
        Priority: longer keywords first (prevents "shop" matching before "shopping mall").
        """
        text = features.all_text
        if not text:
            return None

        for keyword in sorted(KEYWORD_MAP.keys(), key=len, reverse=True):
            if keyword in text:
                return KEYWORD_MAP[keyword], keyword

        return None

    @staticmethod
    def _compute_scores(features: BuildingFeatures) -> Dict[str, float]:
        """
        Apply all heuristic scoring rules to produce per-type scores.

        Returns a dict of building_type → cumulative score (can be negative).
        """
        scores: Dict[str, float] = {t: 0.0 for t in _SCORED_TYPES}

        for rule in SCORING_RULES:
            try:
                if rule.condition(features):
                    for btype, delta in rule.scores.items():
                        scores[btype] = scores.get(btype, 0.0) + delta
            except Exception as exc:  # noqa: BLE001
                logger.debug("Scoring rule '%s' raised: %s", rule.description, exc)

        return scores

    @staticmethod
    def _summarise_features(features: BuildingFeatures) -> List[str]:
        """Build a human-readable list of detected feature signals."""
        signals: List[str] = []
        if features.storeys:
            signals.append(f"storeys={features.storeys}")
        if features.footprint:
            signals.append(f"footprint={features.footprint:.0f}sqm")
        if features.height:
            signals.append(f"height={features.height:.1f}m")
        if features.spaces:
            signals.append(f"spaces={features.spaces}")
        if features.stairs:
            signals.append(f"stairs={features.stairs}")
        if features.num_units is not None:
            signals.append(f"units={features.num_units}")
        if features.has_lift:
            signals.append("has_lift")
        if features.has_loading_dock:
            signals.append("has_loading_dock")
        if features.num_shops:
            signals.append(f"shops={features.num_shops}")
        if features.factory_floor_area:
            signals.append(f"factory_floor={features.factory_floor_area:.0f}sqm")
        return signals

    @staticmethod
    def _determine_method(features: BuildingFeatures) -> str:
        """Return the classification method label for the audit trail."""
        has_geometry = any([
            features.storeys, features.footprint, features.height, features.spaces,
        ])
        has_params = any([
            features.num_units, features.num_shops, features.has_lift,
            features.has_loading_dock, features.factory_floor_area,
        ])
        if has_geometry and has_params:
            return "Geometry + Building Params Heuristic"
        if has_geometry:
            return "Geometry Heuristic"
        if has_params:
            return "Building Params Heuristic"
        return "Heuristic (limited data)"

    @staticmethod
    def _unknown(
        detected: List[str],
        scores: Optional[Dict[str, float]] = None,
    ) -> ClassificationResult:
        return ClassificationResult(
            building_type=BuildingType.UNKNOWN,
            confidence=0.0,
            classification_method="Heuristic (below threshold)",
            detected_features=detected,
            scores={k: round(v, 4) for k, v in scores.items()} if scores else {},
            is_override=False,
        )
