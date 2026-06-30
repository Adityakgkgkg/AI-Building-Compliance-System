"""
AI Building Compliance System — V1 API Router

Aggregates all v1 endpoint routers.
New feature routers (parser, compliance, gis) will be added here in future sprints.
"""

from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.upload import router as upload_router

router = APIRouter(prefix="/api/v1")

# ── Register sub-routers ─────────────────────────────────────────
router.include_router(health_router)
router.include_router(upload_router)

# ── Future Sprint routers ────────────────────────────────────────
# from app.api.v1.parser import router as parser_router
# router.include_router(parser_router)
#
# from app.api.v1.compliance import router as compliance_router
# router.include_router(compliance_router)
#
# from app.api.v1.gis import router as gis_router
# router.include_router(gis_router)
