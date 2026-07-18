import datetime

from pydantic import BaseModel, ConfigDict, Field


class UsernameSearchConfigSchema(BaseModel):
    id: int = Field(..., description="Configuration record ID")
    timeout_seconds: int = Field(..., description="Per-site request timeout in seconds")
    max_concurrency: int = Field(..., description="Maximum concurrent site checks")
    top_sites_count: int = Field(..., description="Number of top-ranked sites to scan (0 = all sites)")
    proxy_url: str | None = Field(default=None, description="Proxy URL used for site checks")
    auto_update_db_enabled: bool = Field(..., description="Whether the site database is refreshed on a schedule")
    auto_update_interval_hours: int = Field(..., description="Hours between site database refresh checks")
    db_last_updated_at: datetime.datetime | None = Field(default=None, description="When the site database was last checked/refreshed")
    db_site_count: int = Field(..., description="Number of sites in the currently loaded database")
    latest_pypi_version: str | None = Field(default=None, description="Latest maigret version published on PyPI, if checked")
    pypi_checked_at: datetime.datetime | None = Field(default=None, description="When PyPI was last checked for a newer maigret version")

    model_config = ConfigDict(from_attributes=True)


class UsernameSearchConfigUpdateSchema(BaseModel):
    timeout_seconds: int | None = Field(default=None, ge=1, le=120, description="Per-site request timeout in seconds")
    max_concurrency: int | None = Field(default=None, ge=1, le=500, description="Maximum concurrent site checks")
    top_sites_count: int | None = Field(default=None, ge=0, le=10000, description="Number of top-ranked sites to scan (0 = all sites)")
    proxy_url: str | None = Field(default=None, max_length=500, description="Proxy URL used for site checks")
    auto_update_db_enabled: bool | None = Field(default=None, description="Whether the site database is refreshed on a schedule")
    auto_update_interval_hours: int | None = Field(default=None, ge=1, le=168, description="Hours between site database refresh checks")
