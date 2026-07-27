"""
AI Building Compliance System — Compliance Service v2

Orchestrates the 5-stage Municipal Rule Engine pipeline:
    1. Stage 1: Building Classification Engine (IFC Metadata -> Geometry -> Heuristics)
    2. Stage 2: Rule Selection Engine (Repository -> Building Type Specific JSONs)
    3. Stage 3: Rule Evaluation Engine (Generic Evaluator + Operators)
    4. Stage 4: Violation Analysis Engine (Enrichment, Priority Sorting, Recommendations)
    5. Stage 5: Compliance Report Generation (Scoring & Formatting)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status

from app.compliance.classification.classifier import BuildingClassifier
from app.compliance.report.report_generator import ReportGenerator
from app.compliance.rule_engine.context_builder import build_context
from app.compliance.rule_engine.evaluator import RuleEvaluator
from app.compliance.rule_selection.loader import RuleLoader, rule_loader as _default_loader
from app.compliance.rule_selection.repository import RuleRepository
from app.compliance.schemas import (
    BuildingParams,
    BuildingType,
    BuildingTypeInfo,
    ClassificationResult,
    ComplianceReport,
    ComplianceRequest,
    RuleDetail,
)

logger = logging.getLogger(__name__)


class ComplianceService:
    """
    Orchestrates the 5-stage BBMP Municipal Rule Engine pipeline.
    """

    def __init__(
        self,
        classifier: Optional[BuildingClassifier] = None,
        repository: Optional[RuleRepository] = None,
        loader: Optional[RuleLoader] = None,
        evaluator: Optional[RuleEvaluator] = None,
        generator: Optional[ReportGenerator] = None,
    ) -> None:
        self._classifier = classifier or BuildingClassifier()
        self._repository = repository or RuleRepository()
        self._loader = loader or _default_loader
        self._evaluator = evaluator or RuleEvaluator()
        self._generator = generator or ReportGenerator()

        # In-memory report cache (file_id -> ComplianceReport)
        self._report_cache: Dict[str, ComplianceReport] = {}

    # ── Primary Pipeline Execution ─────────────────────────────────

    def run_check(self, request: ComplianceRequest) -> ComplianceReport:
        """
        Execute the full 5-stage compliance pipeline.
        """
        logger.info(
            "Compliance check started: file_id=%s override=%s rules_file=%s",
            request.file_id,
            request.override_building_type,
            request.rules_file,
        )

        # Step 0: Resolve parse result
        parse_data = self._resolve_parse_result(request)

        # Stage 1: Building Classification Engine
        classification = self._classifier.classify(
            parse_data=parse_data,
            building_params=request.building_params,
            override=request.override_building_type,
        )

        # Stage 2: Rule Selection Engine
        rule_files = self._select_rules(classification, request.rules_file)
        rules = self._loader.load_many(rule_files)

        # Stage 3: Context Building & Generic Rule Evaluation Engine
        eval_context = build_context(parse_data, request.building_params)
        rule_results = self._evaluator.evaluate_all(rules, eval_context)

        # Stage 4 & 5: Violation Analysis & Report Generation
        params_snapshot = request.building_params.model_dump(exclude_none=False)
        report = self._generator.generate(
            results=rule_results,
            classification=classification,
            loaded_rule_sets=rule_files,
            building_params=params_snapshot,
            file_id=request.file_id,
        )

        # Cache report if file_id present
        if request.file_id:
            self._report_cache[request.file_id] = report
            logger.info(
                "Report cached for file_id=%s: status=%s score=%d",
                request.file_id,
                report.overall_status.value,
                report.compliance_score,
            )

        return report

    # ── Standalone Classification ──────────────────────────────────

    def classify_building(
        self,
        parse_data: Dict[str, Any],
        building_params: Optional[BuildingParams] = None,
    ) -> ClassificationResult:
        """Run Stage 1 classification standalone."""
        return self._classifier.classify(parse_data, building_params)

    # ── Report Retrieval ──────────────────────────────────────────

    def get_cached_report(self, file_id: str) -> ComplianceReport:
        """Retrieve a cached ComplianceReport by file_id."""
        report = self._report_cache.get(file_id)
        if report is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"No compliance report found for file_id '{file_id}'. "
                    "Run POST /api/v1/compliance/check/{file_id} first."
                ),
            )
        return report

    # ── Rules & Metadata Queries ──────────────────────────────────

    def list_rules(self, file_stem: str) -> List[RuleDetail]:
        """List all rules in a specific rule file."""
        try:
            raw_rules = self._loader.load(file_stem)
        except (FileNotFoundError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(exc),
            ) from exc
        return [self._rule_to_detail(r) for r in raw_rules]

    def get_rule(self, file_stem: str, rule_id: str) -> RuleDetail:
        """Get single rule detail by rule_id."""
        rule = self._loader.get_rule(file_stem, rule_id)
        if rule is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rule '{rule_id}' not found in '{file_stem}.json'.",
            )
        return self._rule_to_detail(rule)

    def list_building_types(self) -> List[BuildingTypeInfo]:
        """List all supported building types with descriptions."""
        return [
            BuildingTypeInfo(
                building_type=BuildingType.RESIDENTIAL_HOUSE,
                label="Residential House",
                description="Independent residential houses and villas (G+3 maximum).",
                rule_file="residential_house",
            ),
            BuildingTypeInfo(
                building_type=BuildingType.APARTMENT,
                label="Apartment Complex",
                description="Multi-dwelling residential apartments.",
                rule_file="apartment",
            ),
            BuildingTypeInfo(
                building_type=BuildingType.COMMERCIAL,
                label="Commercial Building",
                description="Offices, retail shops, malls, and showrooms.",
                rule_file="commercial",
            ),
            BuildingTypeInfo(
                building_type=BuildingType.INDUSTRIAL,
                label="Industrial Facility",
                description="Factories, warehouses, and industrial plants.",
                rule_file="industrial",
            ),
            BuildingTypeInfo(
                building_type=BuildingType.INSTITUTIONAL,
                label="Institutional Facility",
                description="Schools, colleges, hospitals, and libraries.",
                rule_file="institutional",
            ),
            BuildingTypeInfo(
                building_type=BuildingType.MIXED_USE,
                label="Mixed-Use Building",
                description="Buildings combining commercial and residential uses.",
                rule_file="mixed_use",
            ),
        ]

    # ── Private Helpers ───────────────────────────────────────────

    def _select_rules(
        self, classification: ClassificationResult, legacy_rules_file: Optional[str]
    ) -> List[str]:
        """Determine rule files to load based on classification or legacy override."""
        if legacy_rules_file:
            return [legacy_rules_file]

        files = self._repository.get_rule_files(classification.building_type)
        if not files and classification.building_type != BuildingType.UNKNOWN:
            # Fallback to residential_house if mapped file doesn't exist
            logger.warning(
                "No rule files mapped for '%s'; falling back to residential_house.",
                classification.building_type.value,
            )
            files = ["residential_house"]
        return files

    def _resolve_parse_result(self, request: ComplianceRequest) -> Dict[str, Any]:
        """Retrieve ParseResult dict from request or parser file_store."""
        if request.parse_result is not None:
            return request.parse_result

        if request.file_id:
            return self._fetch_from_parser_store(request.file_id)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'file_id' or 'parse_result' must be provided.",
        )

    @staticmethod
    def _fetch_from_parser_store(file_id: str) -> Dict[str, Any]:
        try:
            from app.parser.models import file_store  # noqa: PLC0415
            result = file_store.get_result(file_id)
        except ImportError as exc:
            logger.error("Could not import parser store: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal error: parser store unavailable.",
            ) from exc

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"No parse result found for file_id '{file_id}'. "
                    "Please upload and parse the IFC file first via "
                    "POST /api/v1/parser/parse/{file_id}."
                ),
            )

        return result.model_dump()

    @staticmethod
    def _rule_to_detail(rule: dict) -> RuleDetail:
        from app.compliance.schemas import Severity  # noqa: PLC0415
        return RuleDetail(
            rule_id=rule["rule_id"],
            title=rule["title"],
            category=rule["category"],
            building_types=rule.get("building_types", []),
            authority=rule.get("authority", "BBMP"),
            bye_law_reference=rule.get("bye_law_reference"),
            page_number=rule.get("page_number"),
            table_reference=rule.get("table_reference"),
            field=rule.get("field"),
            operator=rule["operator"],
            expected_value=rule["expected_value"],
            unit=rule.get("unit", ""),
            severity=Severity(rule["severity"]),
            priority=rule.get("priority", 1),
            conditions=rule.get("conditions", []),
            required_inputs=rule.get("required_inputs", []),
            formula=rule.get("formula"),
            error_message=rule.get("error_message", ""),
            recommendation=rule.get("recommendation"),
            explanation=rule.get("explanation"),
            is_placeholder=rule.get("is_placeholder", False),
        )
