"""
Tests for Stage 2: Rule Selection Engine.
"""

from __future__ import annotations

import pytest

from app.compliance.rule_selection.loader import RuleLoader
from app.compliance.rule_selection.repository import RuleRepository
from app.compliance.schemas import BuildingType


class TestRuleSelection:
    repo = RuleRepository()
    loader = RuleLoader()

    def test_repository_maps_residential_house(self) -> None:
        files = self.repo.get_rule_files(BuildingType.RESIDENTIAL_HOUSE)
        assert files == ["residential_house"]

    def test_repository_maps_apartment(self) -> None:
        files = self.repo.get_rule_files(BuildingType.APARTMENT)
        assert files == ["apartment"]

    def test_repository_maps_mixed_use(self) -> None:
        files = self.repo.get_rule_files(BuildingType.MIXED_USE)
        assert "residential_house" in files
        assert "commercial" in files

    def test_loader_loads_and_validates_json(self) -> None:
        rules = self.loader.load("residential_house")
        assert isinstance(rules, list)
        assert len(rules) >= 20
        # Verify required keys
        for r in rules:
            assert "rule_id" in r
            assert "expected_value" in r
            assert "operator" in r

    def test_loader_load_many_deduplicates(self) -> None:
        rules = self.loader.load_many(["residential_house", "commercial"])
        ids = [r["rule_id"] for r in rules]
        assert len(ids) == len(set(ids))
