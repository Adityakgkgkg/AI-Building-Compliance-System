"""
AI Building Compliance System — Health Check Endpoint
"""

from fastapi import APIRouter

from app.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Returns the current status of the API server.",
)
async def health_check() -> HealthResponse:
    """Return server health status."""
    return HealthResponse(status="running")
