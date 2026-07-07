import datetime

from pydantic import BaseModel, ConfigDict, Field


class SocialAnalyzerConfigSchema(BaseModel):
    id: int = Field(..., description="Configuration record ID")
    timeout_seconds: int = Field(..., description="Delay between requests in seconds (social-analyzer's own throttling)")
    top_sites_count: int = Field(..., description="Number of top-ranked sites to scan (0 = all sites)")
    latest_pypi_version: str | None = Field(default=None, description="Latest social-analyzer version published on PyPI, if checked")
    pypi_checked_at: datetime.datetime | None = Field(default=None, description="When PyPI was last checked for a newer version")

    model_config = ConfigDict(from_attributes=True)


class SocialAnalyzerConfigUpdateSchema(BaseModel):
    timeout_seconds: int | None = Field(default=None, ge=0, le=120, description="Delay between requests in seconds (social-analyzer's own throttling)")
    top_sites_count: int | None = Field(default=None, ge=0, description="Number of top-ranked sites to scan (0 = all sites)")
