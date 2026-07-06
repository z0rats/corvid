from datetime import datetime
from typing import Any
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class IOCType(str, Enum):
    """Supported IOC types for lookup"""
    IPV4 = "ipv4"
    IPV6 = "ipv6"
    DOMAIN = "domain"
    URL = "url"
    MD5 = "md5"
    SHA1 = "sha1"
    SHA256 = "sha256"
    EMAIL = "email"
    CVE = "cve"
    EVM_ADDRESS = "evm_address"
    BITCOIN_ADDRESS = "bitcoin_address"
    UNKNOWN = "unknown"


class LookupStatus(str, Enum):
    """Status of a lookup operation"""
    SUCCESS = "success"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"
    UNAUTHORIZED = "unauthorized"
    SERVICE_UNAVAILABLE = "service_unavailable"


class ServiceInfo(BaseModel):
    """Information about a lookup service"""
    key: str = Field(..., description="Unique service identifier")
    name: str = Field(..., description="Human-readable service name")
    supported_ioc_types: list[str] = Field(..., description="List of supported IOC types")
    is_configured: bool = Field(..., description="Whether service is properly configured")
    is_bulk_enabled: bool = Field(default=False, description="Whether bulk lookup is enabled")
    required_keys: list[str] = Field(default_factory=list, description="Required API keys")
    is_available: bool = Field(default=True, description="Whether service is currently available")
    icon: str | None = Field(None, description="Service icon identifier")


class LookupResult(BaseModel):
    """Result of a single IOC lookup"""
    ioc: str = Field(..., description="The IOC that was looked up")
    service: str = Field(..., description="Service that performed the lookup")
    status: LookupStatus = Field(..., description="Status of the lookup")
    data: dict[str, Any] | None = Field(None, description="Lookup result data")
    error: str | None = Field(None, description="Error message if lookup failed")
    timestamp: datetime | None = Field(None, description="Timestamp of the lookup")


class SingleLookupRequest(BaseModel):
    """Request for single IOC lookup"""
    ioc: str = Field(..., description="IOC value to lookup", min_length=1)
    ioc_type: IOCType | None = Field(None, description="IOC type (auto-detected if not provided)")
    service: str = Field(..., description="Service to use for lookup")

    @field_validator('ioc')
    @classmethod
    def validate_ioc_not_empty(cls, v: str) -> str:
        """Ensure IOC is not just whitespace"""
        if not v.strip():
            raise ValueError("IOC cannot be empty or contain only whitespace")
        return v.strip()


class BulkLookupRequest(BaseModel):
    """Request for bulk IOC lookup"""
    iocs: list[str] = Field(..., description="List of IOCs to lookup", min_length=1, max_length=1000)
    services: list[str] = Field(..., description="List of services to use", min_length=1)

    @field_validator('iocs')
    @classmethod
    def validate_iocs_not_empty(cls, v: list[str]) -> list[str]:
        """Ensure IOCs are not empty"""
        cleaned_iocs = []
        for ioc in v:
            if isinstance(ioc, str) and ioc.strip():
                cleaned_iocs.append(ioc.strip())

        if not cleaned_iocs:
            raise ValueError("At least one valid IOC must be provided")

        return cleaned_iocs


class ServicesResponse(BaseModel):
    """Response containing available services"""
    services: list[ServiceInfo] = Field(..., description="List of available services")


class ServiceDefinitionsResponse(BaseModel):
    """Response containing service definitions"""
    serviceDefinitions: dict[str, dict[str, Any]] = Field(..., description="Service definitions")


class IOCTypesResponse(BaseModel):
    """Response containing supported IOC types"""
    types: dict[str, str] = Field(..., description="Supported IOC types")


class LookupErrorResponse(BaseModel):
    """Error response for lookup operations"""
    error: str | int = Field(..., description="Error code or message")
    message: str = Field(..., description="Error description")
    details: str | None = Field(None, description="Additional error details")
    supported_types: list[str] | None = Field(None, description="Supported IOC types for service")
    available_services: list[str] | None = Field(None, description="Available services")
