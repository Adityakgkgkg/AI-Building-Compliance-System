"""
AI-Driven Context-Aware System for Automated Building Plan Compliance
and 3D Urban Integration

FastAPI Application Entry Point
================================
- Mounts the v1 API router
- Configures CORS for the Next.js frontend
- Initializes the database on startup
- Provides interactive API docs at /docs
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.database import init_db
from app.api.v1 import router as v1_router

settings = get_settings()


# ── Lifespan ─────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    # Startup
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    init_db()
    settings.upload_path  # Ensure upload directory exists
    print(f"📁 Upload directory: {settings.upload_path.resolve()}")
    yield
    # Shutdown
    print("👋 Shutting down...")


# ── App ──────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AI-driven system for automated building plan compliance checking "
        "and 3D urban integration. This API provides endpoints for file "
        "upload, compliance analysis, and GIS context integration."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── CORS ─────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global Exception Handler ────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch unhandled exceptions and return a clean 500 response."""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred.",
            "error": str(exc) if settings.DEBUG else "Internal Server Error",
        },
    )


# ── Mount Routers ────────────────────────────────────────────────
app.include_router(v1_router)


# ── Root Redirect ────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint redirects to API documentation."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/v1/health",
    }
