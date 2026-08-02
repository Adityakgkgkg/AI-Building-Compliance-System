"""
MCRDSE Analysis Orchestrator – Service Layer
============================================
``OrchestratorService`` orchestrates the automated end-to-end compliance workflow:
Parser -> Classification -> GIS Context -> Compliance Engine -> Evidence Collector -> Decision Support -> Export Engine.

Rules:
- NO business logic re-implementation.
- Uses existing service classes exclusively.
- Immediate stopping upon any upstream stage failure.
- Measures wall-clock execution timing per stage.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

from app.compliance.classification.service import ClassificationService
from app.compliance.rule_engine.service import ComplianceEngineService
from app.decision.service import DecisionService
from app.export.service import ExportService
from app.gis.schemas import GISContextRequest
from app.gis.service import GISService
from app.orchestrator.exceptions import StageExecutionError
from app.orchestrator.models import AnalysisRecord
from app.orchestrator.schemas import AnalysisProgressResponse, UnifiedAnalysisResponse
from app.orchestrator.utils import elapsed_ms, generate_analysis_id, get_stage_progress, perf_start
from app.parser.service import IFCParserService
from app.parser.utils import get_uploads_dir
from app.report.evidence_collector import EvidenceCollector
from app.report.schemas import ModuleErrorDetail

logger = logging.getLogger("app.orchestrator.service")

# In-memory progress tracking store for active runs
_PROGRESS_STORE: Dict[str, AnalysisProgressResponse] = {}
_RESULTS_STORE: Dict[str, UnifiedAnalysisResponse] = {}


class OrchestratorService:
    """
    Orchestration facade running end-to-end building compliance analysis.
    """

    @classmethod
    def get_progress(cls, analysis_id: str) -> Optional[AnalysisProgressResponse]:
        """Fetch current execution progress for an analysis run."""
        return _PROGRESS_STORE.get(analysis_id)

    @classmethod
    def get_result(cls, analysis_id: str) -> Optional[UnifiedAnalysisResponse]:
        """Fetch completed unified analysis response for an analysis run."""
        return _RESULTS_STORE.get(analysis_id)

    @classmethod
    def analyze_ifc(
        cls,
        ifc_file_bytes: bytes,
        filename: str,
        lat: float = 12.9250,
        lon: float = 77.5938,
        host_base_url: str = "http://localhost:8000",
        db: Optional[object] = None,
    ) -> Union[UnifiedAnalysisResponse, Tuple[ModuleErrorDetail, int]]:
        """
        Execute automated end-to-end compliance analysis workflow.

        Parameters
        ----------
        ifc_file_bytes:
            Raw bytes of the uploaded .ifc file.
        filename:
            Filename of the IFC file.
        lat:
            WGS84 latitude.
        lon:
            WGS84 longitude.
        host_base_url:
            Host base URL for export verification links.
        db:
            Optional DB session.

        Returns
        -------
        UnifiedAnalysisResponse or (ModuleErrorDetail, status_code)
        """
        t0 = perf_start()
        analysis_id = generate_analysis_id()
        stage_timings: Dict[str, float] = {}

        def update_stage(stage_name: str, status_str: str = "running", err: Optional[Dict[str, Any]] = None):
            prog = get_stage_progress(stage_name)
            prog_obj = AnalysisProgressResponse(
                analysis_id=analysis_id,
                status=status_str,
                current_stage=stage_name,
                progress=prog,
                error=err,
            )
            _PROGRESS_STORE[analysis_id] = prog_obj
            logger.info("[%s] Stage: %s | Progress: %d%%", analysis_id[:8], stage_name, prog)

        # ── 1. Upload & File Save ──────────────────────────────────────────────
        update_stage("Uploading")
        upload_path = get_uploads_dir() / filename
        try:
            upload_path.write_bytes(ifc_file_bytes)
        except Exception as exc:
            err = ModuleErrorDetail(error_code="UPLOAD_FAILED", module="orchestrator", detail=f"Failed to save upload file: {exc}")
            update_stage("Uploading", status_str="failed", err=err.model_dump(mode="json"))
            return err, 400

        # ── 2. Parser Engine (Module 1) ────────────────────────────────────────
        update_stage("Parsing IFC")
        t_step = perf_start()
        try:
            building_ev = IFCParserService.parse(upload_path)
            stage_timings["parser"] = elapsed_ms(t_step)
        except Exception as exc:
            logger.error("[%s] Parser failed: %s", analysis_id[:8], exc)
            err = ModuleErrorDetail(error_code="PARSER_MODULE_UNAVAILABLE", module="ifc_parser", detail=str(exc))
            update_stage("Parsing IFC", status_str="failed", err=err.model_dump(mode="json"))
            return err, 503

        # ── 3. Extract Geometry (Module 1 Sub-engine) ─────────────────────────
        update_stage("Extracting Geometry")
        t_step = perf_start()
        try:
            geom = IFCParserService.extract_geometry(upload_path)
            stage_timings["geometry"] = elapsed_ms(t_step)
        except Exception as exc:
            logger.warning("[%s] Geometry extraction warning: %s", analysis_id[:8], exc)
            stage_timings["geometry"] = elapsed_ms(t_step)

        # ── 4. Building Classification (Module 2) ──────────────────────────────
        update_stage("Building Classification")
        t_step = perf_start()
        try:
            classification_res = ClassificationService.classify(building_ev)
            stage_timings["classification"] = elapsed_ms(t_step)
        except Exception as exc:
            logger.error("[%s] Classification failed: %s", analysis_id[:8], exc)
            err = ModuleErrorDetail(error_code="CLASSIFICATION_MODULE_UNAVAILABLE", module="classification", detail=str(exc))
            update_stage("Building Classification", status_str="failed", err=err.model_dump(mode="json"))
            return err, 503

        # ── 5. GIS Context Engine (Module 3) ──────────────────────────────────
        update_stage("GIS Analysis")
        t_step = perf_start()
        try:
            gis_res = GISService.get_full_context(GISContextRequest(latitude=lat, longitude=lon))
            stage_timings["gis"] = elapsed_ms(t_step)
        except Exception as exc:
            logger.error("[%s] GIS Engine failed: %s", analysis_id[:8], exc)
            err = ModuleErrorDetail(error_code="GIS_ENGINE_UNAVAILABLE", module="gis_context", detail=str(exc))
            update_stage("GIS Analysis", status_str="failed", err=err.model_dump(mode="json"))
            return err, 503

        # ── 6. Compliance Engine (Module 2) ───────────────────────────────────
        update_stage("Compliance Checking")
        t_step = perf_start()
        try:
            compliance_res = ComplianceEngineService.evaluate(building_ev, gis_res)
            stage_timings["compliance"] = elapsed_ms(t_step)
        except Exception as exc:
            logger.error("[%s] Compliance Engine failed: %s", analysis_id[:8], exc)
            err = ModuleErrorDetail(error_code="COMPLIANCE_MODULE_UNAVAILABLE", module="compliance_engine", detail=str(exc))
            update_stage("Compliance Checking", status_str="failed", err=err.model_dump(mode="json"))
            return err, 503

        # ── 7. Evidence Collection (Module 4 Sprint 1) ───────────────────────
        update_stage("Evidence Collection")
        t_step = perf_start()
        try:
            collector = EvidenceCollector()
            bundle = collector.build_bundle(ifc_file=filename, lat=lat, lon=lon)
            stage_timings["evidence"] = elapsed_ms(t_step)
        except Exception as exc:
            logger.error("[%s] Evidence Collection failed: %s", analysis_id[:8], exc)
            err = ModuleErrorDetail(error_code="BUNDLE_ASSEMBLY_FAILED", module="evidence_collector", detail=str(exc))
            update_stage("Evidence Collection", status_str="failed", err=err.model_dump(mode="json"))
            return err, 503

        # ── 8. Decision Support Engine (Module 4 Sprint 3) ───────────────────
        update_stage("Decision Support")
        t_step = perf_start()
        try:
            decision_ctx_res = DecisionService.get_decision_context(ifc_file=filename, lat=lat, lon=lon, bundle=bundle)
            if isinstance(decision_ctx_res, tuple):
                err_detail, status_code = decision_ctx_res
                update_stage("Decision Support", status_str="failed", err=err_detail.model_dump(mode="json"))
                return decision_ctx_res
            decision_ctx = decision_ctx_res
            stage_timings["decision"] = elapsed_ms(t_step)
        except Exception as exc:
            logger.error("[%s] Decision Engine failed: %s", analysis_id[:8], exc)
            err = ModuleErrorDetail(error_code="DECISION_ENGINE_FAILED", module="decision_support", detail=str(exc))
            update_stage("Decision Support", status_str="failed", err=err.model_dump(mode="json"))
            return err, 503

        # ── 9. Export Engine (Module 4 Sprint 4) ─────────────────────────────
        update_stage("Generating Report")
        t_step = perf_start()
        try:
            export_res_or_err = ExportService.generate_report(
                ifc_file=filename,
                lat=lat,
                lon=lon,
                requested_formats=["pdf", "html", "json"],
                host_base_url=host_base_url,
                db=db,
            )
            if isinstance(export_res_or_err, tuple):
                err_detail, status_code = export_res_or_err
                update_stage("Generating Report", status_str="failed", err=err_detail.model_dump(mode="json"))
                return export_res_or_err
            export_res = export_res_or_err
            stage_timings["export"] = elapsed_ms(t_step)
        except Exception as exc:
            logger.error("[%s] Export Engine failed: %s", analysis_id[:8], exc)
            err = ModuleErrorDetail(error_code="EXPORT_ENGINE_FAILED", module="export_engine", detail=str(exc))
            update_stage("Generating Report", status_str="failed", err=err.model_dump(mode="json"))
            return err, 503

        # ── 10. Completion & Unified Response Assembly ────────────────────────
        update_stage("Completed", status_str="completed")
        total_time = elapsed_ms(t0)

        dashboard_url = f"/dashboard?analysis_id={analysis_id}&ifc_file={filename}&lat={lat}&lon={lon}"
        report_url = f"/api/v1/export/pdf/{export_res.report_id}"

        classification_dict = {
            "predicted_type": classification_res.predicted_type,
            "confidence": classification_res.confidence,
            "reason": classification_res.reason,
        }

        compliance_dict = {
            "rules_checked": compliance_res.rules_checked,
            "passed": compliance_res.passed,
            "failed": compliance_res.failed,
            "warnings": compliance_res.warnings,
            "blocking": compliance_res.blocking,
            "score": compliance_res.score,
            "rule_results": [r.__dict__ for r in compliance_res.rule_results],
        }

        unified_response = UnifiedAnalysisResponse(
            analysis_id=analysis_id,
            status="completed",
            current_stage="Completed",
            progress=100,
            building=building_ev.model_dump(mode="json"),
            classification=classification_dict,
            gis=gis_res.model_dump(mode="json"),
            compliance=compliance_dict,
            evidence=bundle.model_dump(mode="json"),
            decision=decision_ctx.model_dump(mode="json"),
            reports=export_res.model_dump(mode="json"),
            dashboard_url=dashboard_url,
            report_url=report_url,
            processing_time=stage_timings,
            total_processing_time=total_time,
        )

        _RESULTS_STORE[analysis_id] = unified_response

        # Persist audit record in DB if session provided
        if db is not None:
            try:
                rec = AnalysisRecord(
                    analysis_id=analysis_id,
                    ifc_file=filename,
                    status="completed",
                    current_stage="Completed",
                    progress=100,
                    building_id=building_ev.building_id,
                    building_name=building_ev.building_name,
                    sanction_verdict=decision_ctx.approval.sanction_verdict,
                    compliance_score=compliance_res.score,
                    total_processing_time_ms=total_time,
                )
                db.add(rec)  # type: ignore[union-attr]
                db.commit()  # type: ignore[union-attr]
            except Exception as exc:
                logger.warning("[%s] Failed to persist AnalysisRecord: %s", analysis_id[:8], exc)

        logger.info(
            "[%s] Analysis completed successfully | verdict='%s' | elapsed=%.2f ms",
            analysis_id[:8],
            decision_ctx.approval.sanction_verdict[:50],
            total_time,
        )

        return unified_response
