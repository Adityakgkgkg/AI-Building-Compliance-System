"""
Tests for Stage 1: Building Classification Engine.
"""

from __future__ import annotations

import pytest

from app.compliance.classification.classifier import BuildingClassifier
from app.compliance.classification.features import extract_features
from app.compliance.schemas import BuildingParams, BuildingType


class TestBuildingClassifier:
    clf = BuildingClassifier()

    def test_override_takes_precedence(self, minimal_parse_result: dict) -> None:
        res = self.clf.classify(
            minimal_parse_result, override=BuildingType.COMMERCIAL
        )
        assert res.building_type == BuildingType.COMMERCIAL
        assert res.confidence == 1.0
        assert res.is_override is True
        assert res.classification_method == "Override"

    def test_metadata_keyword_matching_apartment(
        self, apartment_parse_result: dict
    ) -> None:
        res = self.clf.classify(apartment_parse_result)
        assert res.building_type == BuildingType.APARTMENT
        assert res.confidence >= 0.90
        assert res.classification_method == "IFC Metadata"

    def test_metadata_keyword_matching_residential_house(
        self, minimal_parse_result: dict
    ) -> None:
        res = self.clf.classify(minimal_parse_result)
        assert res.building_type == BuildingType.RESIDENTIAL_HOUSE
        assert res.confidence >= 0.90

    def test_heuristic_classification_without_metadata(self) -> None:
        # Strip text metadata to force heuristic scoring
        no_text_parse = {
            "building": {"storeys": 2},
            "elements": {"spaces": 5, "stairs": 1},
            "geometry": {"footprint": 120.0, "height": 7.0},
        }
        res = self.clf.classify(no_text_parse)
        assert res.building_type == BuildingType.RESIDENTIAL_HOUSE
        assert "Heuristic" in res.classification_method

    def test_heuristic_classification_commercial(self) -> None:
        params = BuildingParams(num_shops=4, num_offices=2, building_use="commercial")
        no_text_parse = {
            "building": {"storeys": 4},
            "elements": {"spaces": 25, "doors": 40},
            "geometry": {"footprint": 800.0, "height": 14.0},
        }
        res = self.clf.classify(no_text_parse, building_params=params)
        assert res.building_type == BuildingType.COMMERCIAL

    def test_unknown_classification_when_no_signals(self) -> None:
        empty_parse = {"building": {}, "elements": {}, "geometry": {}}
        res = self.clf.classify(empty_parse)
        assert res.building_type == BuildingType.UNKNOWN
        assert res.confidence == 0.0



