import time
from typing import Any

from fastapi import APIRouter, Request, Response, status

from app.core.dependencies import DatabaseHealthDep, SettingsDep
from app.core.healthcheck_schemas import (
    DetailedHealthResponse,
    HealthResponse,
    LivenessResponse,
    ReadinessResponse,
)

router = APIRouter(prefix="/api/healthcheck", tags=["System"])


def _format_uptime(startup_time: float | None) -> str:
    """Format uptime as a human-readable string"""
    if startup_time is None:
        return "starting"
    elapsed = int(time.time() - startup_time)
    days, remainder = divmod(elapsed, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return " ".join(parts)


def determine_overall_status(services: dict[str, Any]) -> str:
    """Determine overall system health based on service statuses"""
    database_status = services.get("database", {}).get("status", "unhealthy")
    return "healthy" if database_status == "healthy" else "unhealthy"


@router.get(
    "",
    response_model=HealthResponse,
    summary="Basic health check",
    description="Returns basic health status including database connectivity",
    responses={503: {"description": "Service unhealthy"}},
)
async def basic_healthcheck(
    request: Request,
    settings: SettingsDep,
    database_health: DatabaseHealthDep,
    response: Response,
) -> HealthResponse:
    """Return basic service status, version, and timestamp"""
    health_status = "ok" if database_health.get("status") == "healthy" else "unhealthy"

    if health_status == "unhealthy":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    startup_time = getattr(request.app.state, "startup_time", None)
    return HealthResponse(
        status=health_status,
        version=settings.api.version,
        timestamp=time.time(),
        uptime=_format_uptime(startup_time),
    )


@router.get(
    "/detailed",
    response_model=DetailedHealthResponse,
    summary="Detailed health check",
    description="Returns detailed health status including database connectivity",
    responses={503: {"description": "Service degraded or unhealthy"}},
)
async def detailed_healthcheck(
    request: Request,
    settings: SettingsDep,
    database_health: DatabaseHealthDep,
    response: Response,
) -> DetailedHealthResponse:
    """Return comprehensive health information including database status"""

    services = {
        "database": database_health,
        "api": {
            "status": "healthy",
            "name": settings.api.title,
            "version": settings.api.version,
        },
    }

    overall_status = determine_overall_status(services)

    if overall_status in ("degraded", "unhealthy"):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    startup_time = getattr(request.app.state, "startup_time", None)
    return DetailedHealthResponse(
        status=overall_status,
        version=settings.api.version,
        timestamp=time.time(),
        uptime=_format_uptime(startup_time),
        services=services,
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness probe",
    description="Kubernetes/Docker readiness probe endpoint",
    responses={503: {"description": "Service not ready"}},
)
async def readiness_probe(database_health: DatabaseHealthDep, response: Response) -> ReadinessResponse:
    """Return 200 if service is ready to accept traffic, 503 otherwise"""

    if database_health.get("status") == "healthy":
        return ReadinessResponse(ready=True)

    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(ready=False, reason="Database not available")


@router.get(
    "/live",
    response_model=LivenessResponse,
    summary="Liveness probe",
    description="Kubernetes/Docker liveness probe endpoint",
)
async def liveness_probe() -> LivenessResponse:
    """Return 200 if service is alive, regardless of dependencies"""
    return LivenessResponse(alive=True, timestamp=time.time())
