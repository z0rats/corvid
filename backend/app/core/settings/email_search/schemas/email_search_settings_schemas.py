import datetime

from pydantic import BaseModel, ConfigDict, Field


class EmailSearchConfigSchema(BaseModel):
    id: int = Field(..., description="Configuration record ID")
    timeout_seconds: int = Field(..., description="Per-provider request timeout in seconds")
    max_concurrency: int = Field(..., description="Maximum concurrent provider checks")
    proxy_url: str | None = Field(default=None, description="Proxy URL used for provider checks")
    use_tor: bool = Field(..., description="Route provider checks through a local Tor SOCKS5 proxy (127.0.0.1:9050)")
    enable_smtp_checks: bool = Field(..., description="Enable SMTP-based checks (Gmail, Yandex, mail.de) - needs outbound TCP/25, usually via Tor or proxy")
    enable_headless_checks: bool = Field(..., description="Enable headless-Chromium-based checks (Fastmail, int.pl, onet.pl) - downloads a Chromium binary on first use")
    latest_pypi_version: str | None = Field(default=None, description="Latest mailcat-osint version published on PyPI, if checked")
    pypi_checked_at: datetime.datetime | None = Field(default=None, description="When PyPI was last checked for a newer version")

    model_config = ConfigDict(from_attributes=True)


class EmailSearchConfigUpdateSchema(BaseModel):
    timeout_seconds: int | None = Field(default=None, ge=1, le=60, description="Per-provider request timeout in seconds")
    max_concurrency: int | None = Field(default=None, ge=1, le=50, description="Maximum concurrent provider checks")
    proxy_url: str | None = Field(default=None, max_length=500, description="Proxy URL used for provider checks")
    use_tor: bool | None = Field(default=None, description="Route provider checks through a local Tor SOCKS5 proxy (127.0.0.1:9050)")
    enable_smtp_checks: bool | None = Field(default=None, description="Enable SMTP-based checks (Gmail, Yandex, mail.de)")
    enable_headless_checks: bool | None = Field(default=None, description="Enable headless-Chromium-based checks (Fastmail, int.pl, onet.pl)")
