"""
AI Building Compliance System — Core Validators Package

Exports base validator interface and specific domain validators.
In v2, all rule evaluation is driven by the generic rule engine
and rules repository JSON files.
"""

from __future__ import annotations

from typing import Any, Dict


class BaseValidator:
    """Base validator interface for custom specialized validators if needed."""
    def validate(self, context: Dict[str, Any], rule: dict) -> bool:
        return True
