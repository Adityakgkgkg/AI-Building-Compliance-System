"""
AI Building Compliance System — Evaluation Operators

Pure functions implementing all supported rule comparison operators.
No BBMP-specific knowledge — purely generic comparisons.

Each operator function signature:
    operator_fn(actual: Any, rule: dict) -> OperatorResult

Supported operators:
    gte, lte, gt, lt, eq, ne       — numeric comparison
    between                        — expected_value is [min, max]
    in_range                       — inclusive [min, max] range
    exists                         — field is not None/False/0/empty
    not_exists                     — field is None/False/0/empty
    matches                        — string contains expected substring
    calculated                     — actual is pre-computed (pass-through comparison)
    all_gte                        — every item in a list is >= expected
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class OperatorResult:
    """Result of applying an operator."""
    passed: bool
    actual: Any
    expected: Any
    difference: Optional[float] = None
    message: str = ""


def _safe_float(value: Any) -> Optional[float]:
    """Coerce value to float, returning None on failure."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _diff(actual: Any, expected: Any) -> Optional[float]:
    """Compute actual - expected as float, or None if not numeric."""
    a = _safe_float(actual)
    e = _safe_float(expected)
    if a is not None and e is not None:
        return round(a - e, 6)
    return None


# ── Individual operator implementations ───────────────────────────

def op_gte(actual: Any, rule: dict) -> OperatorResult:
    expected = rule["expected_value"]
    a = _safe_float(actual)
    e = _safe_float(expected)
    if a is None or e is None:
        return OperatorResult(False, actual, expected, message="Non-numeric value for ≥ comparison.")
    passed = a >= e
    return OperatorResult(passed=passed, actual=a, expected=e, difference=round(a - e, 6))


def op_lte(actual: Any, rule: dict) -> OperatorResult:
    expected = rule["expected_value"]
    a = _safe_float(actual)
    e = _safe_float(expected)
    if a is None or e is None:
        return OperatorResult(False, actual, expected, message="Non-numeric value for ≤ comparison.")
    passed = a <= e
    return OperatorResult(passed=passed, actual=a, expected=e, difference=round(a - e, 6))


def op_gt(actual: Any, rule: dict) -> OperatorResult:
    expected = rule["expected_value"]
    a = _safe_float(actual)
    e = _safe_float(expected)
    if a is None or e is None:
        return OperatorResult(False, actual, expected, message="Non-numeric value for > comparison.")
    passed = a > e
    return OperatorResult(passed=passed, actual=a, expected=e, difference=round(a - e, 6))


def op_lt(actual: Any, rule: dict) -> OperatorResult:
    expected = rule["expected_value"]
    a = _safe_float(actual)
    e = _safe_float(expected)
    if a is None or e is None:
        return OperatorResult(False, actual, expected, message="Non-numeric value for < comparison.")
    passed = a < e
    return OperatorResult(passed=passed, actual=a, expected=e, difference=round(a - e, 6))


def op_eq(actual: Any, rule: dict) -> OperatorResult:
    expected = rule["expected_value"]
    a = _safe_float(actual)
    e = _safe_float(expected)
    if a is not None and e is not None:
        passed = abs(a - e) < 1e-9
        return OperatorResult(passed=passed, actual=a, expected=e, difference=round(a - e, 6))
    passed = actual == expected
    return OperatorResult(passed=passed, actual=actual, expected=expected)


def op_ne(actual: Any, rule: dict) -> OperatorResult:
    expected = rule["expected_value"]
    a = _safe_float(actual)
    e = _safe_float(expected)
    if a is not None and e is not None:
        passed = abs(a - e) >= 1e-9
        return OperatorResult(passed=passed, actual=a, expected=e, difference=round(a - e, 6))
    passed = actual != expected
    return OperatorResult(passed=passed, actual=actual, expected=expected)


def op_between(actual: Any, rule: dict) -> OperatorResult:
    """
    expected_value must be [min, max].
    Passes if min <= actual <= max.
    """
    expected = rule["expected_value"]
    if not isinstance(expected, (list, tuple)) or len(expected) != 2:
        return OperatorResult(
            False, actual, expected,
            message="'between' operator requires expected_value=[min, max]."
        )
    lo, hi = expected
    a = _safe_float(actual)
    lo_f, hi_f = _safe_float(lo), _safe_float(hi)
    if a is None or lo_f is None or hi_f is None:
        return OperatorResult(False, actual, expected, message="Non-numeric value for between.")
    passed = lo_f <= a <= hi_f
    return OperatorResult(passed=passed, actual=a, expected=expected)


def op_in_range(actual: Any, rule: dict) -> OperatorResult:
    """Alias for between (inclusive range)."""
    return op_between(actual, rule)


def op_exists(actual: Any, rule: dict) -> OperatorResult:
    """Passes if actual is not None, not False, not 0, not empty string."""
    passed = actual is not None and actual is not False and actual != 0 and actual != ""
    return OperatorResult(passed=passed, actual=actual, expected=True)


def op_not_exists(actual: Any, rule: dict) -> OperatorResult:
    """Passes if actual is None, False, 0, or empty string."""
    passed = actual is None or actual is False or actual == 0 or actual == ""
    return OperatorResult(passed=passed, actual=actual, expected=False)


def op_matches(actual: Any, rule: dict) -> OperatorResult:
    """Passes if actual string contains expected_value as a substring (case-insensitive)."""
    expected = rule["expected_value"]
    if actual is None:
        return OperatorResult(False, actual, expected, message="Field is None.")
    passed = str(expected).lower() in str(actual).lower()
    return OperatorResult(passed=passed, actual=actual, expected=expected)


def op_calculated(actual: Any, rule: dict) -> OperatorResult:
    """
    The actual value is a pre-computed expression from the context.
    Compare it against expected_value using the same gte logic.
    (The 'formula' field was already resolved by the context builder.)
    """
    return op_gte(actual, rule)


def op_all_gte(actual: Any, rule: dict) -> OperatorResult:
    """
    actual must be a list. All values must be >= expected_value.
    Reports the minimum value as the 'actual' in the result.
    """
    expected = rule["expected_value"]
    e = _safe_float(expected)
    if e is None:
        return OperatorResult(False, actual, expected, message="Non-numeric expected_value.")
    if not isinstance(actual, (list, tuple)) or len(actual) == 0:
        return OperatorResult(False, actual, expected, message="Expected a non-empty list.")

    floats = [_safe_float(v) for v in actual]
    if any(v is None for v in floats):
        return OperatorResult(False, actual, expected, message="List contains non-numeric value.")

    min_val = min(floats)  # type: ignore[arg-type]
    passed = min_val >= e
    return OperatorResult(
        passed=passed,
        actual=min_val,
        expected=e,
        difference=round(min_val - e, 6),
    )


# ── Operator dispatch table ───────────────────────────────────────

OPERATOR_MAP: Dict[str, Callable[[Any, dict], OperatorResult]] = {
    "gte":        op_gte,
    "lte":        op_lte,
    "gt":         op_gt,
    "lt":         op_lt,
    "eq":         op_eq,
    "ne":         op_ne,
    "between":    op_between,
    "in_range":   op_in_range,
    "exists":     op_exists,
    "not_exists": op_not_exists,
    "matches":    op_matches,
    "calculated": op_calculated,
    "all_gte":    op_all_gte,
}


def evaluate_operator(operator: str, actual: Any, rule: dict) -> OperatorResult:
    """
    Dispatch to the correct operator function.

    Args:
        operator: Operator name string (e.g. "gte").
        actual:   Actual value from evaluation context.
        rule:     Rule dict (for expected_value and unit).

    Returns:
        OperatorResult.

    Raises:
        ValueError: Unknown operator.
    """
    fn = OPERATOR_MAP.get(operator)
    if fn is None:
        raise ValueError(
            f"Unknown operator '{operator}'. "
            f"Supported: {sorted(OPERATOR_MAP.keys())}"
        )
    return fn(actual, rule)
