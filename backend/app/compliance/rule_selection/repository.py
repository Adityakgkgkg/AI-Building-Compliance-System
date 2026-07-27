"""
AI Building Compliance System — Rule Repository

Maps BuildingType → list of rule file paths.

Stage 2 of the pipeline: given a ClassificationResult, the repository
returns exactly which rule JSON files to load. Only relevant rules
are ever loaded — no building type ever evaluates rules for another type.

Rule file resolution order (for mixed-use / fallback):
  1. Exact type match
  2. Combined sets (e.g., mixed_use loads both residential + commercial sets)
  3. Empty list for UNKNOWN (no rules loaded → INSUFFICIENT_DATA)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional

from app.compliance.schemas import BuildingType

logger = logging.getLogger(__name__)

# Absolute path to rules/ directory (sibling of compliance/)
_RULES_ROOT: Path = Path(__file__).parent.parent / "rules" / "bbmp"


class RuleRepository:
    """
    Maps a BuildingType to the list of rule file stems to load.

    The repository is the only place that knows which JSON files exist
    and what building type they serve.
    """

    # Mapping: BuildingType → list of rule file stems (relative to _RULES_ROOT)
    _TYPE_TO_FILES: Dict[str, List[str]] = {
        BuildingType.RESIDENTIAL_HOUSE.value: ["residential_house"],
        BuildingType.APARTMENT.value:         ["apartment"],
        BuildingType.COMMERCIAL.value:        ["commercial"],
        BuildingType.INDUSTRIAL.value:        ["industrial"],
        BuildingType.INSTITUTIONAL.value:     ["institutional"],
        BuildingType.MIXED_USE.value:         ["residential_house", "commercial"],  # Both apply
        BuildingType.PUBLIC_SEMI_PUBLIC.value: ["institutional"],                  # Closest match
        BuildingType.UNKNOWN.value:           [],  # No rules for unknown
    }

    def __init__(self, rules_root: Optional[Path] = None) -> None:
        self._rules_root = rules_root or _RULES_ROOT

    def get_rule_files(self, building_type: BuildingType) -> List[str]:
        """
        Return list of rule file stems for the given building type.

        Args:
            building_type: Classified (or overridden) building type.

        Returns:
            List of file stems (without .json) to be loaded by the loader.
        """
        files = self._TYPE_TO_FILES.get(building_type.value, [])
        if not files:
            logger.warning(
                "No rule files mapped for building type '%s'.",
                building_type.value,
            )
        else:
            logger.debug(
                "Rule files for '%s': %s", building_type.value, files
            )
        return files

    def list_available_building_types(self) -> List[str]:
        """Return building types that have at least one rule file mapped."""
        return [
            bt
            for bt, files in self._TYPE_TO_FILES.items()
            if files
        ]

    def get_rule_file_path(self, stem: str) -> Path:
        """Return the absolute path to a rule file by stem."""
        return self._rules_root / f"{stem}.json"

    def list_available_files(self) -> List[str]:
        """Return all existing rule file stems in the rules directory."""
        if not self._rules_root.exists():
            return []
        return [p.stem for p in self._rules_root.glob("*.json")]
