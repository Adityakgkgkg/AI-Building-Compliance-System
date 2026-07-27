"""
AI Building Compliance System — Rule Evaluator

Stage 3 of the Municipal Rule Engine pipeline.

The evaluator is completely generic — it knows nothing about BBMP.
It evaluates rules by:
  1. Checking conditions (field/operator/value guards)
  2. Checking required_inputs (SKIP if missing)
  3. Resolving the actual value from context (field or formula-alias)
  4. Applying the operator (via operators.py)
  5. Returning a RuleResult

Placeholder rules are evaluated but capped at WARNING severity.
Validator exceptions are caught and returned as SKIPPED results.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.compliance.rule_engine.operators import OperatorResult, evaluate_operator
from app.compliance.schemas import RuleResult, RuleStatus, Severity

logger = logging.getLogger(__name__)

# Computed alias fields — rules can reference these instead of a formula
_COMPUTED_ALIASES: Dict[str, str] = {
    "far":                 "far",
    "ground_coverage_pct": "ground_coverage_pct",
    "parking_ratio":       "parking_ratio",
    "min_storey_height":   "min_storey_height",
    "min_side_setback":    "min_side_setback",
    "min_setback":         "min_setback",
    "open_space_ratio":    "open_space_ratio",
    "is_high_rise":        "is_high_rise",
    "is_very_high_rise":   "is_very_high_rise",
    "storey_heights":      "storey_heights",
}


class RuleEvaluator:
    """
    Generic, stateless rule evaluator.

    Usage::

        evaluator = RuleEvaluator()
        results = evaluator.evaluate_all(rules, context)
    """

    def evaluate_all(
        self,
        rules: List[dict],
        context: Dict[str, Any],
    ) -> List[RuleResult]:
        """
        Evaluate every rule against the evaluation context.

        Args:
            rules:   List of validated rule dicts from the rule loader.
            context: Flat EvaluationContext dict from context_builder.

        Returns:
            List of RuleResult (one per rule, in input order).
        """
        results: List[RuleResult] = []
        for rule in rules:
            result = self._evaluate_one(rule, context)
            results.append(result)

        passed   = sum(1 for r in results if r.status == RuleStatus.PASSED)
        failed   = sum(1 for r in results if r.status == RuleStatus.FAILED)
        warnings = sum(1 for r in results if r.status == RuleStatus.WARNING)
        na       = sum(1 for r in results if r.status == RuleStatus.NOT_APPLICABLE)
        skipped  = sum(1 for r in results if r.status == RuleStatus.SKIPPED)

        logger.info(
            "Evaluation: total=%d passed=%d failed=%d warn=%d na=%d skip=%d",
            len(results), passed, failed, warnings, na, skipped,
        )
        return results

    # ── Private ───────────────────────────────────────────────────

    def _evaluate_one(
        self, rule: dict, context: Dict[str, Any]
    ) -> RuleResult:
        """Evaluate a single rule — never raises."""
        rule_id   = rule.get("rule_id", "UNKNOWN")
        severity  = Severity(rule.get("severity", "error"))

        try:
            return self._do_evaluate(rule, context, severity)
        except Exception as exc:
            logger.exception("Evaluator error for rule '%s': %s", rule_id, exc)
            return self._make_result(
                rule=rule,
                status=RuleStatus.SKIPPED,
                severity=severity,
                message=f"Evaluator raised an unexpected error: {exc}",
            )

    def _do_evaluate(
        self,
        rule: dict,
        context: Dict[str, Any],
        severity: Severity,
    ) -> RuleResult:
        rule_id     = rule["rule_id"]
        is_placeholder = rule.get("is_placeholder", False)

        # ── Step 1: Evaluate conditions ───────────────────────────
        na_reason = self._check_conditions(rule.get("conditions", []), context)
        if na_reason is not None:
            return self._make_result(
                rule=rule,
                status=RuleStatus.NOT_APPLICABLE,
                severity=severity,
                message=na_reason,
            )

        # ── Step 2: Check required_inputs ─────────────────────────
        skip_reason = self._check_required_inputs(
            rule.get("required_inputs", []), context
        )
        if skip_reason is not None:
            return self._make_result(
                rule=rule,
                status=RuleStatus.SKIPPED,
                severity=severity,
                message=skip_reason,
            )

        # ── Step 3: Resolve actual value ──────────────────────────
        field_name = rule.get("field", "")
        actual = self._resolve_field(field_name, context, rule)
        if actual is None and not rule.get("operator") in ("exists", "not_exists"):
            return self._make_result(
                rule=rule,
                status=RuleStatus.SKIPPED,
                severity=severity,
                message=(
                    f"Field '{field_name}' is not available in the evaluation context. "
                    "Provide the required data in building_params."
                ),
            )

        # ── Step 4: Apply operator ────────────────────────────────
        operator = rule["operator"]
        op_result: OperatorResult = evaluate_operator(operator, actual, rule)

        # ── Step 5: Build result ──────────────────────────────────
        if op_result.passed:
            return self._make_result(
                rule=rule,
                status=RuleStatus.PASSED,
                severity=severity,
                actual=op_result.actual,
                expected=op_result.expected,
                difference=op_result.difference,
                message=self._pass_message(rule, op_result),
            )

        # Failed — placeholder rules capped at WARNING
        effective_severity = severity
        if is_placeholder and severity == Severity.ERROR:
            effective_severity = Severity.WARNING

        fail_status = (
            RuleStatus.WARNING
            if effective_severity == Severity.WARNING
            else RuleStatus.FAILED
        )

        return self._make_result(
            rule=rule,
            status=fail_status,
            severity=effective_severity,
            actual=op_result.actual,
            expected=op_result.expected,
            difference=op_result.difference,
            message=self._fail_message(rule, op_result),
        )

    @staticmethod
    def _check_conditions(
        conditions: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> Optional[str]:
        """
        Evaluate rule conditions.

        Each condition: {"field": str, "operator": str, "value": Any}
        If any condition fails, return a reason string → NOT_APPLICABLE.
        """
        for cond in conditions:
            cfield = cond.get("field", "")
            cop    = cond.get("operator", "gte")
            cval   = cond.get("value")

            ctx_val = context.get(cfield)
            if ctx_val is None:
                # Can't evaluate condition — rule is NOT_APPLICABLE
                return (
                    f"Condition field '{cfield}' not in context. "
                    f"Rule not applicable without this information."
                )

            # Build a synthetic rule for the condition check
            cond_rule = {"expected_value": cval, "unit": ""}
            try:
                op_result = evaluate_operator(cop, ctx_val, cond_rule)
                if not op_result.passed:
                    return (
                        f"Condition not met: '{cfield}' {cop} {cval} "
                        f"(actual={ctx_val}). Rule is not applicable."
                    )
            except Exception:  # noqa: BLE001
                return f"Condition evaluation error for field '{cfield}'."

        return None  # All conditions passed

    @staticmethod
    def _check_required_inputs(
        required_inputs: List[str],
        context: Dict[str, Any],
    ) -> Optional[str]:
        """
        Check that all required_inputs are present and non-null.
        Returns a skip reason string if any are missing.
        """
        missing = [
            f for f in required_inputs
            if context.get(f) is None
        ]
        if missing:
            return (
                f"Required input(s) not provided: {missing}. "
                "Add these fields to building_params."
            )
        return None

    @staticmethod
    def _resolve_field(
        field_name: str,
        context: Dict[str, Any],
        rule: dict,
    ) -> Any:
        """
        Resolve the field value from context.

        For 'calculated' operator, the formula is a pre-computed context alias.
        """
        if not field_name:
            return None

        # Direct context lookup
        value = context.get(field_name)
        if value is not None:
            return value

        # Try computed aliases
        alias = _COMPUTED_ALIASES.get(field_name)
        if alias:
            return context.get(alias)

        return None

    @staticmethod
    def _pass_message(rule: dict, op: OperatorResult) -> str:
        unit = rule.get("unit", "")
        if op.actual is not None and op.expected is not None:
            return (
                f"{rule['title']}: {op.actual} {unit} "
                f"meets the requirement of {op.expected} {unit}."
            )
        return f"{rule['title']}: requirement met."

    @staticmethod
    def _fail_message(rule: dict, op: OperatorResult) -> str:
        template = rule.get("error_message", "")
        if template:
            return (
                template
                .replace("{actual}", str(op.actual))
                .replace("{expected}", str(op.expected))
                .replace("{unit}", rule.get("unit", ""))
            )
        unit = rule.get("unit", "")
        return (
            f"{rule['title']}: actual={op.actual} {unit}, "
            f"required={op.expected} {unit}."
        )

    @staticmethod
    def _make_result(
        rule: dict,
        status: RuleStatus,
        severity: Severity,
        actual: Any = None,
        expected: Any = None,
        difference: Optional[float] = None,
        message: Optional[str] = None,
    ) -> RuleResult:
        return RuleResult(
            rule_id=rule["rule_id"],
            title=rule["title"],
            category=rule["category"],
            status=status,
            severity=severity,
            priority=rule.get("priority", 1),
            authority=rule.get("authority", "BBMP"),
            bye_law_reference=rule.get("bye_law_reference"),
            page_number=rule.get("page_number"),
            table_reference=rule.get("table_reference"),
            is_placeholder=rule.get("is_placeholder", False),
            expected=expected,
            actual=actual,
            difference=difference,
            unit=rule.get("unit"),
            message=message,
            explanation=rule.get("explanation"),
            recommendation=rule.get("recommendation"),
        )
