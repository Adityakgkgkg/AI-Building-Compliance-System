"""
MCRDSE Sprint 1 – Pure Utility Functions
=========================================
Stateless helper functions used across the report module.

Design rules:
- Every function is pure: same inputs → same outputs, no side effects.
- No business logic.  No imports from other report sub-modules (to prevent
  circular dependencies).
- All functions are independently unit-testable.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone


def generate_report_id() -> str:
    """
    Generate a UUID4 string to uniquely identify an evidence collection run.

    Returns
    -------
    str
        A lowercase hyphenated UUID4 string, e.g.
        ``'3fa85f64-5717-4562-b3fc-2c963f66afa6'``.
    """
    return str(uuid.uuid4())


def utc_now() -> datetime:
    """
    Return the current UTC datetime with timezone information attached.

    Returns
    -------
    datetime
        Timezone-aware ``datetime`` in UTC.
    """
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    """
    Return the current UTC datetime as an ISO 8601 string.

    Returns
    -------
    str
        UTC timestamp in the form ``'2026-07-28T17:45:00.123456+00:00'``.
    """
    return utc_now().isoformat()


def elapsed_ms(start: float) -> float:
    """
    Calculate elapsed wall-clock time in milliseconds since *start*.

    Parameters
    ----------
    start:
        A ``time.perf_counter()`` snapshot taken before the operation.

    Returns
    -------
    float
        Elapsed time in milliseconds, rounded to two decimal places.
    """
    return round((time.perf_counter() - start) * 1_000.0, 2)


def perf_start() -> float:
    """
    Capture a high-resolution performance counter snapshot.

    Convenience wrapper around ``time.perf_counter()`` so callers do not need
    to import ``time`` directly.

    Returns
    -------
    float
        Opaque monotonic counter value suitable for passing to
        :func:`elapsed_ms`.
    """
    return time.perf_counter()
