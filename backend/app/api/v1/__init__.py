"""
AI Building Compliance System — V1 API Router

Aggregates all v1 endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.upload import router as upload_router
from app.decision.router import router as decision_router
from app.export.router import router as export_router
from app.gis.router import router as gis_router
from app.orchestrator.router import router as orchestrator_router
from app.parser.router import router as parser_router
from app.report.router import router as report_router

router = APIRouter(prefix="/api/v1")

# ── Register sub-routers ─────────────────────────────────────────
router.include_router(health_router)
router.include_router(upload_router)
router.include_router(orchestrator_router)# Automated Analysis Orchestrator
router.include_router(parser_router)    # Module 1 – IFC Parser Engine
router.include_router(gis_router)        # Module 3 – GIS Context Engine
router.include_router(report_router)    # Module 4 Sprint 1 – MCRDSE Evidence Collection
router.include_router(decision_router)  # Module 4 Sprint 3 – MCRDSE Decision Support
router.include_router(export_router)    # Module 4 Sprint 4 – MCRDSE Reporting & Export Engine
