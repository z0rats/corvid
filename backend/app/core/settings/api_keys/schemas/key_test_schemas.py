from enum import StrEnum

from pydantic import BaseModel, Field


class KeyTestStatus(StrEnum):
    OK = "ok"
    REJECTED = "rejected"
    RATE_LIMITED = "rate_limited"
    PLAN_REQUIRED = "plan_required"
    UNREACHABLE = "unreachable"
    ERROR = "error"
    NOT_CONFIGURED = "not_configured"
    UNTESTABLE = "untestable"


class KeyQuota(BaseModel):
    """Allowance left on the key, for providers whose test call reports it."""

    used: int | None = Field(default=None, description="Requests used in the current period")
    limit: int | None = Field(default=None, description="Total allowed in the current period")
    remaining: int | None = Field(default=None, description="Remaining requests/credits")
    period: str | None = Field(default=None, description="e.g. 'daily', 'monthly', 'hourly'")


class KeyTestResult(BaseModel):
    """Outcome of one live key check. `detail` is always our own text, never the provider's
    response, so a key echoed back by a provider can't reach the client."""

    service: str = Field(..., description="Service key from the services config")
    status: KeyTestStatus
    http_status: int | None = Field(default=None, description="Provider's HTTP status, if any")
    detail: str = Field(..., description="What the status means and what to do about it")
    quota: KeyQuota | None = None
