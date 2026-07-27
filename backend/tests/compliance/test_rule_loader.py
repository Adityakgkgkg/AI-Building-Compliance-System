"""
Tests for RuleLoader.

Covers:
  - Loading the real bbmp_2003_residential.json
  - Caching (same list object returned on second call)
  - get_rule() by rule_id
  - get_meta() returns meta block
  - FileNotFoundError on missing file
  - ValueError on duplicate rule IDs (tested with patched data)
  - ValueError on invalid JSON
  - invalidate() clears cache
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from app.compliance.rule_loader import RuleLoader


class TestRuleLoaderRealFile:
    """Tests against the actual bbmp_2003_residential.json."""

    def setup_method(self) -> None:
        self.loader = RuleLoader()

    def test_load_returns_list(self) -> None:
        rules = self.loader.load("residential_house")
        assert isinstance(rules, list)
        assert len(rules) > 0

    def test_load_is_cached(self) -> None:
        rules1 = self.loader.load("residential_house")
        rules2 = self.loader.load("residential_house")
        assert rules1 is rules2  # Same object → cached

    def test_rules_have_required_fields(self) -> None:
        rules = self.loader.load("residential_house")
        required = {
            "rule_id", "title", "category", "building_types",
            "operator", "expected_value", "unit", "severity", "error_message",
        }
        for rule in rules:
            missing = required - rule.keys()
            assert not missing, f"Rule {rule.get('rule_id')} missing: {missing}"

    def test_get_rule_existing(self) -> None:
        rule = self.loader.get_rule("residential_house", "BBMP-RES-P001")
        assert rule is not None
        assert rule["rule_id"] == "BBMP-RES-P001"
        assert rule["title"] == "Minimum Plot Area"

    def test_get_rule_missing(self) -> None:
        rule = self.loader.get_rule("residential_house", "NONEXISTENT-RULE")
        assert rule is None

    def test_get_meta_returns_authority(self) -> None:
        meta = self.loader.get_meta("residential_house")
        assert meta.get("authority") == "BBMP"
        assert meta.get("bye_laws") == "2003"

    def test_all_rule_ids_unique(self) -> None:
        rules = self.loader.load("residential_house")
        ids = [r["rule_id"] for r in rules]
        assert len(ids) == len(set(ids)), "Duplicate rule IDs found"

    def test_all_severities_valid(self) -> None:
        rules = self.loader.load("residential_house")
        valid = {"error", "warning", "info"}
        for rule in rules:
            assert rule["severity"] in valid, (
                f"Rule {rule['rule_id']} has invalid severity: {rule['severity']}"
            )

    def test_list_rule_files(self) -> None:
        files = self.loader.list_rule_files()
        assert "residential_house" in files

    def test_invalidate_clears_cache(self) -> None:
        self.loader.load("residential_house")
        self.loader.invalidate("residential_house")
        # After invalidation, re-load should work
        rules = self.loader.load("residential_house")
        assert len(rules) > 0



class TestRuleLoaderErrors:
    """Tests for error handling with custom rules directories."""

    def _make_loader_with_dir(self, rules_dir: Path) -> RuleLoader:
        return RuleLoader(rules_dir=rules_dir)

    def test_missing_file_raises_file_not_found(self, tmp_path: Path) -> None:
        loader = self._make_loader_with_dir(tmp_path)
        with pytest.raises(FileNotFoundError, match="not found"):
            loader.load("nonexistent_rules")

    def test_invalid_json_raises_value_error(self, tmp_path: Path) -> None:
        bad_file = tmp_path / "bad_rules.json"
        bad_file.write_text("NOT VALID JSON }{", encoding="utf-8")
        loader = self._make_loader_with_dir(tmp_path)
        with pytest.raises(ValueError, match="Invalid JSON"):
            loader.load("bad_rules")

    def test_duplicate_rule_ids_raises_value_error(self, tmp_path: Path) -> None:
        data = {
            "_meta": {"authority": "TEST"},
            "rules": [
                {
                    "rule_id": "TEST-001",
                    "title": "Test Rule",
                    "category": "Test",
                    "building_types": ["residential_house"],
                    "field": "plot_area",
                    "operator": "gte",
                    "expected_value": 10,
                    "unit": "m",
                    "severity": "error",
                    "error_message": "Test message",
                },
                {
                    "rule_id": "TEST-001",  # Duplicate!
                    "title": "Duplicate Rule",
                    "category": "Test",
                    "building_types": ["residential_house"],
                    "field": "plot_area",
                    "operator": "gte",
                    "expected_value": 20,
                    "unit": "m",
                    "severity": "error",
                    "error_message": "Another message",
                },
            ],
        }

        rules_file = tmp_path / "dup_rules.json"
        rules_file.write_text(json.dumps(data), encoding="utf-8")
        loader = self._make_loader_with_dir(tmp_path)
        with pytest.raises(ValueError, match="Duplicate"):
            loader.load("dup_rules")

    def test_missing_required_field_raises(self, tmp_path: Path) -> None:
        data = {
            "_meta": {},
            "rules": [
                {
                    "rule_id": "TEST-001",
                    "title": "Missing Fields Rule",
                    # Missing: category, applies_to, operator, etc.
                }
            ],
        }
        rules_file = tmp_path / "missing_fields.json"
        rules_file.write_text(json.dumps(data), encoding="utf-8")
        loader = self._make_loader_with_dir(tmp_path)
        with pytest.raises(ValueError, match="missing required fields"):
            loader.load("missing_fields")
