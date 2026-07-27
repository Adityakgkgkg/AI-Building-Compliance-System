"""
AI Building Compliance System — Rule Selection Loader

Thread-safe JSON rule loader with caching and schema validation.

Loads rule definitions from JSON files in rules/bbmp/, validates them,
and caches the parsed result. Cache is invalidated per file stem.

Required fields for every rule (strictly enforced at load time):
  rule_id, title, category, building_types, field, operator,
  expected_value, unit, severity, error_message
"""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Fields every rule MUST have — validated at load time
_REQUIRED_FIELDS = {
    "rule_id",
    "title",
    "category",
    "building_types",
    "field",
    "operator",
    "expected_value",
    "unit",
    "severity",
    "error_message",
}

_VALID_SEVERITIES = {"error", "warning", "info"}
_VALID_OPERATORS = {
    "gte", "lte", "gt", "lt", "eq", "ne",
    "between", "in_range",
    "exists", "not_exists",
    "matches",
    "calculated",
    "all_gte",
}


class RuleLoader:
    """
    Thread-safe loader for BBMP rule JSON files.

    Usage::

        loader = RuleLoader()
        rules = loader.load("apartment")        # loads rules/bbmp/apartment.json
        meta  = loader.get_meta("apartment")
        rule  = loader.get_rule("apartment", "BBMP-APT-P001")
    """

    def __init__(self, rules_root: Optional[Path] = None, rules_dir: Optional[Path] = None) -> None:
        from app.compliance.rule_selection.repository import _RULES_ROOT
        self._rules_root: Path = rules_root or rules_dir or _RULES_ROOT
        self._cache: Dict[str, List[dict]] = {}
        self._meta_cache: Dict[str, dict] = {}
        self._lock = threading.RLock()

    def list_rule_files(self) -> List[str]:
        """Backward compatibility alias for list_files."""
        return self.list_files()

    # ── Public API ────────────────────────────────────────────────

    def load(self, file_stem: str) -> List[dict]:
        """
        Load and return all rules from *file_stem*.json (cached).

        Args:
            file_stem: File name without .json (e.g. "apartment").

        Returns:
            Validated list of rule dicts.

        Raises:
            FileNotFoundError: File does not exist.
            ValueError: JSON error or schema violation.
        """
        with self._lock:
            if file_stem not in self._cache:
                rules, meta = self._load_from_disk(file_stem)
                self._cache[file_stem] = rules
                self._meta_cache[file_stem] = meta
                logger.info(
                    "Loaded %d rules from '%s.json'", len(rules), file_stem
                )
            return self._cache[file_stem]

    def load_many(self, file_stems: List[str]) -> List[dict]:
        """
        Load rules from multiple files and deduplicate by rule_id.

        Rules from later files override earlier ones with the same rule_id.
        """
        all_rules: Dict[str, dict] = {}
        for stem in file_stems:
            for rule in self.load(stem):
                all_rules[rule["rule_id"]] = rule
        return list(all_rules.values())

    def get_meta(self, file_stem: str) -> dict:
        """Return the _meta section of a rule file."""
        self.load(file_stem)
        with self._lock:
            return self._meta_cache.get(file_stem, {})

    def get_rule(self, file_stem: str, rule_id: str) -> Optional[dict]:
        """Return a single rule dict by rule_id, or None."""
        for rule in self.load(file_stem):
            if rule["rule_id"] == rule_id:
                return rule
        return None

    def list_files(self) -> List[str]:
        """List available rule file stems in the rules directory."""
        if not self._rules_root.exists():
            return []
        return [p.stem for p in self._rules_root.glob("*.json")]

    def invalidate(self, file_stem: Optional[str] = None) -> None:
        """Clear the cache (for testing / hot-reload)."""
        with self._lock:
            if file_stem:
                self._cache.pop(file_stem, None)
                self._meta_cache.pop(file_stem, None)
            else:
                self._cache.clear()
                self._meta_cache.clear()

    # ── Private ───────────────────────────────────────────────────

    def _load_from_disk(self, file_stem: str) -> Tuple[List[dict], dict]:
        path = self._rules_root / f"{file_stem}.json"
        if not path.exists():
            available = self.list_files()
            raise FileNotFoundError(
                f"Rule file '{file_stem}.json' not found in {self._rules_root}. "
                f"Available: {available}"
            )

        try:
            with path.open(encoding="utf-8") as fh:
                data = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid JSON in '{file_stem}.json': {exc}"
            ) from exc

        if not isinstance(data, dict):
            raise ValueError(f"'{file_stem}.json' must be a JSON object at root.")

        meta: dict = data.get("_meta", {})
        raw_rules: list = data.get("rules", [])

        if not isinstance(raw_rules, list):
            raise ValueError(f"'rules' in '{file_stem}.json' must be a JSON array.")

        validated: List[dict] = []
        for idx, rule in enumerate(raw_rules):
            validated.append(self._validate_rule(rule, idx, file_stem))

        # Duplicate rule_id check
        ids = [r["rule_id"] for r in validated]
        dups = {rid for rid in ids if ids.count(rid) > 1}
        if dups:
            raise ValueError(
                f"Duplicate rule_ids in '{file_stem}.json': {dups}"
            )

        return validated, meta

    @staticmethod
    def _validate_rule(rule: dict, idx: int, stem: str) -> dict:
        if not isinstance(rule, dict):
            raise ValueError(f"Rule at index {idx} in '{stem}.json' is not an object.")

        missing = _REQUIRED_FIELDS - rule.keys()
        if missing:
            rid = rule.get("rule_id", f"<index {idx}>")
            raise ValueError(
                f"Rule '{rid}' in '{stem}.json' missing required fields: {missing}"
            )

        if rule["severity"] not in _VALID_SEVERITIES:
            raise ValueError(
                f"Rule '{rule['rule_id']}': invalid severity '{rule['severity']}'."
            )

        if rule["operator"] not in _VALID_OPERATORS:
            raise ValueError(
                f"Rule '{rule['rule_id']}': unknown operator '{rule['operator']}'."
            )

        if not isinstance(rule["building_types"], list):
            raise ValueError(
                f"Rule '{rule['rule_id']}': 'building_types' must be a list."
            )

        # Apply defaults
        rule.setdefault("is_placeholder", False)
        rule.setdefault("explanation", "")
        rule.setdefault("recommendation", "")
        rule.setdefault("conditions", [])
        rule.setdefault("required_inputs", [])
        rule.setdefault("formula", None)
        rule.setdefault("priority", 1)
        rule.setdefault("authority", "BBMP")
        rule.setdefault("bye_law_reference", "")
        rule.setdefault("page_number", None)
        rule.setdefault("table_reference", "")

        return rule


# ── Module-level singleton ────────────────────────────────────────
rule_loader = RuleLoader()
