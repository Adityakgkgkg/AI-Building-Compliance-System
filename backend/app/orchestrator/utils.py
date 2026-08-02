"""
MCRDSE Analysis Orchestrator – Utilities
========================================
Progress mapping and timing utilities.
"""

from __future__ import annotations

import time
import uuid
from typing import Dict

STAGE_PROGRESS_MAP: Dict[str, int] = {
    "Uploading": 5,
    "Parsing IFC": 20,
    "Extracting Geometry": 35,
    "Building Classification": 50,
    "GIS Analysis": 65,
    "Compliance Checking": 75,
    "Evidence Collection": 85,
    "Decision Support": 92,
    "Generating Report": 98,
    "Completed": 100,
}


def generate_analysis_id() -> str:
    """Generate unique UUID4 for analysis run."""
    return str(uuid.uuid4())


def get_stage_progress(stage_name: str) -> int:
    """Return completion percentage for stage name."""
    return STAGE_PROGRESS_MAP.get(stage_name, 50)


def perf_start() -> float:
    """Return monotonic start time."""
    return time.perf_counter()


def elapsed_ms(t0: float) -> float:
    """Return elapsed wall-clock time in ms."""
    return round((time.perf_counter() - t0) * 1000.0, 2)
