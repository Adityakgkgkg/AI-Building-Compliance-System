"""
MCRDSE Analysis Orchestrator – Domain Exception Hierarchy
==========================================================
Typed exceptions for workflow orchestration failures.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class OrchestrationError(Exception):
    """Base exception for analysis orchestration errors."""

    def __init__(self, message: str, stage: str = "Initialization", code: str = "ORCHESTRATION_ERROR", detail: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.stage = stage
        self.code = code
        self.detail = detail or message

    def as_dict(self) -> Dict[str, Any]:
        return {
            "error_code": self.code,
            "stage": self.stage,
            "message": self.message,
            "detail": self.detail,
        }


class StageExecutionError(OrchestrationError):
    """Raised when an individual module stage fails during orchestration."""

    def __init__(self, stage: str, module_name: str, detail: str):
        message = f"Analysis failed during stage '{stage}' ({module_name}): {detail}"
        super().__init__(message=message, stage=stage, code=f"{module_name.upper()}_STAGE_FAILED", detail=detail)
        self.module_name = module_name
