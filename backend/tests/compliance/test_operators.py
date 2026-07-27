"""
Tests for Evaluation Operators.
"""

from __future__ import annotations

import pytest

from app.compliance.rule_engine.operators import evaluate_operator


class TestOperators:

    def test_op_gte(self) -> None:
        rule = {"expected_value": 10.0}
        res = evaluate_operator("gte", 15.0, rule)
        assert res.passed is True
        assert res.difference == 5.0

        res_fail = evaluate_operator("gte", 5.0, rule)
        assert res_fail.passed is False
        assert res_fail.difference == -5.0

    def test_op_lte(self) -> None:
        rule = {"expected_value": 2.5}
        res = evaluate_operator("lte", 2.0, rule)
        assert res.passed is True

        res_fail = evaluate_operator("lte", 3.0, rule)
        assert res_fail.passed is False

    def test_op_between(self) -> None:
        rule = {"expected_value": [5.0, 15.0]}
        assert evaluate_operator("between", 10.0, rule).passed is True
        assert evaluate_operator("between", 4.0, rule).passed is False
        assert evaluate_operator("between", 16.0, rule).passed is False

    def test_op_exists(self) -> None:
        rule = {"expected_value": True}
        assert evaluate_operator("exists", True, rule).passed is True
        assert evaluate_operator("exists", "installed", rule).passed is True
        assert evaluate_operator("exists", None, rule).passed is False

    def test_op_all_gte(self) -> None:
        rule = {"expected_value": 2.75}
        assert evaluate_operator("all_gte", [3.0, 3.2, 2.8], rule).passed is True
        assert evaluate_operator("all_gte", [3.0, 2.5, 3.0], rule).passed is False

    def test_op_unknown_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown operator"):
            evaluate_operator("invalid_op", 10, {"expected_value": 5})

