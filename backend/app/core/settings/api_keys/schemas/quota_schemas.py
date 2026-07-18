from pydantic import BaseModel, Field


class QuotaStatus(BaseModel):
    """Quota/usage snapshot for one provider, as of the moment it was checked."""

    provider: str = Field(..., description="API key name this quota belongs to")
    configured: bool = Field(..., description="Whether an API key is configured for this provider")
    used: int | None = Field(default=None, description="Requests used in the current period, if reported")
    limit: int | None = Field(default=None, description="Total allowed requests in the current period, if reported")
    remaining: int | None = Field(default=None, description="Remaining requests/credits, if reported")
    period: str | None = Field(default=None, description="Quota period/kind, e.g. 'daily', 'monthly'")
    error: str | None = Field(default=None, description="Set if the quota check failed for this provider")
