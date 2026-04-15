from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Basic health check response"""
    status: str = Field(..., description="Overall health status")
    version: str = Field(..., description="Application version")
    timestamp: float = Field(..., description="Current server timestamp")
    uptime: str = Field(..., description="Service uptime information")


class DetailedHealthResponse(BaseModel):
    """Detailed health check response including service statuses"""
    status: str = Field(..., description="Overall health status")
    version: str = Field(..., description="Application version")
    timestamp: float = Field(..., description="Current server timestamp")
    uptime: str = Field(..., description="Service uptime information")
    services: dict[str, Any] = Field(..., description="Individual service health status")


class ReadinessResponse(BaseModel):
    """Readiness probe response"""
    ready: bool = Field(..., description="Whether the service is ready to accept traffic")
    reason: str | None = Field(None, description="Reason if the service is not ready")


class LivenessResponse(BaseModel):
    """Liveness probe response"""
    alive: bool = Field(..., description="Whether the service process is alive")
    timestamp: float = Field(..., description="Current server timestamp")
