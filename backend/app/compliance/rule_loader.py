"""
AI Building Compliance System — Rule Loader Stub (v1 backwards compatibility)

In v2, rule loading is handled by app.compliance.rule_selection.loader.
This module is maintained as an alias for backwards compatibility.
"""

from app.compliance.rule_selection.loader import RuleLoader, rule_loader

__all__ = ["RuleLoader", "rule_loader"]
