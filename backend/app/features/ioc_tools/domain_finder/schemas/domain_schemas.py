import logging
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class DomainLookupRequest(BaseModel):
    """Request model for domain lookup operations"""

    domain: str = Field(
        ...,
        description="Domain name to lookup (e.g., 'example.com')",
        min_length=1,
        max_length=255
    )

    @field_validator('domain')
    @classmethod
    def validate_domain_format(cls, v: str) -> str:
        """Validate domain format and perform basic sanitization"""
        logger.debug("Schema validation for domain: '%s'", v)

        if not v or not v.strip():
            logger.warning("Empty domain provided in schema validation")
            raise ValueError('Domain cannot be empty')

        domain = v.strip().lower()

        if domain.startswith(('http://', 'https://')):
            domain = domain.split('://', 1)[1]

        if '/' in domain:
            domain = domain.split('/', 1)[0]

        if len(domain) > 255:
            logger.error("Domain too long in schema validation: '%s' (length: %s)", domain, len(domain))
            raise ValueError('Domain name too long')

        if any(char in domain for char in [' ', '\t', '\n', '\r']):
            logger.error("Invalid characters in domain: '%s'", domain)
            raise ValueError('Domain contains invalid characters')

        logger.debug("Schema validation successful: '%s' -> '%s'", v, domain)
        return domain


class UrlScanResult(BaseModel):
    """Individual URL scan result from urlscan.io API."""

    task: dict[str, Any] | None = Field(default=None, description="Task information from the scan")
    stats: dict[str, Any] | None = Field(default=None, description="Statistics from the scan")
    page: dict[str, Any] | None = Field(default=None, description="Page information from the scan")
    lists: dict[str, Any] | None = Field(default=None, description="Lists information from the scan")
    verdicts: dict[str, Any] | None = Field(default=None, description="Verdicts from the scan")
    meta: dict[str, Any] | None = Field(default=None, description="Metadata from the scan")
    expanded: bool = Field(default=False, description="Whether the result is expanded in the UI")


class DomainLookupResponse(BaseModel):
    """Response model for domain lookup operations."""

    domain: str = Field(..., description="The domain that was looked up")
    results: list[UrlScanResult] = Field(..., description="List of scan results from urlscan.io")
    total_results: int = Field(..., description="Total number of results found", ge=0)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the lookup was performed"
    )


class DomainLookupError(BaseModel):
    """Error response model for domain lookup operations."""

    domain: str = Field(..., description="The domain that failed to be looked up")
    error_type: str = Field(..., description="Type of error that occurred")
    error_message: str = Field(..., description="Detailed error message")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the error occurred"
    )
