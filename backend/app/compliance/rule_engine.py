"""
AI Building Compliance System — Rule Engine Stub (v1 backwards compatibility)

In v2, evaluation is handled by app.compliance.rule_engine.evaluator.
This module is maintained as an alias for backwards compatibility.
"""

from app.compliance.rule_engine.evaluator import RuleEvaluator as RuleEngine

__all__ = ["RuleEngine"]
