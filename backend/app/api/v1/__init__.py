"""
AI Building Compliance System — V1 API Router

Aggregates all v1 endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.upload import router as upload_router
from app.parser import router as parser_router          # Module 1: IFC Parser
from app.compliance import router as compliance_router  # Module 2: Compliance Engine

router = APIRouter(prefix="/api/v1")

# ── Register sub-routers ─────────────────────────────────────────
router.include_router(health_router)
router.include_router(upload_router)
router.include_router(parser_router)      # Module 1: /api/v1/parser/*
router.include_router(compliance_router)  # Module 2: /api/v1/compliance/*

# ── Future Sprint routers ────────────────────────────────────────
# from app.api.v1.gis import router as gis_router
# router.include_router(gis_router)  # Module 3: /api/v1/gis/*
