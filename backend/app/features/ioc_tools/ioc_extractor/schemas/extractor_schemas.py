from pydantic import BaseModel, Field, field_validator
from typing import Any


class TextExtractionRequest(BaseModel):
    """Request schema for text-based IOC extraction"""
    text: str = Field(..., description="Text content to extract IOCs from", min_length=1)

    @field_validator('text')
    @classmethod
    def validate_text_not_empty(cls, v: str) -> str:
        """Ensure text is not just whitespace"""
        if not v.strip():
            raise ValueError("Text cannot be empty or contain only whitespace")
        return v.strip()


class IOCStatistics(BaseModel):
    """Statistics about extracted IOCs"""
    ips: int = Field(default=0, description="Number of IP addresses found")
    md5: int = Field(default=0, description="Number of MD5 hashes found")
    sha1: int = Field(default=0, description="Number of SHA1 hashes found")
    sha256: int = Field(default=0, description="Number of SHA256 hashes found")
    urls: int = Field(default=0, description="Number of URLs found")
    domains: int = Field(default=0, description="Number of domains found")
    emails: int = Field(default=0, description="Number of email addresses found")
    cves: int = Field(default=0, description="Number of CVE identifiers found")
    ips_removed_duplicates: int = Field(default=0, description="Number of duplicate IPs removed")
    md5_removed_duplicates: int = Field(default=0, description="Number of duplicate MD5s removed")
    sha1_removed_duplicates: int = Field(default=0, description="Number of duplicate SHA1s removed")
    sha256_removed_duplicates: int = Field(default=0, description="Number of duplicate SHA256s removed")
    urls_removed_duplicates: int = Field(default=0, description="Number of duplicate URLs removed")
    domains_removed_duplicates: int = Field(default=0, description="Number of duplicate domains removed")
    emails_removed_duplicates: int = Field(default=0, description="Number of duplicate emails removed")
    cves_removed_duplicates: int = Field(default=0, description="Number of duplicate CVEs removed")
    total_unique_iocs: int = Field(default=0, description="Total number of unique IOCs found")


class ExtractionResponse(BaseModel):
    """Response schema for IOC extraction"""
    ips: list[str] = Field(default_factory=list, description="Extracted IP addresses")
    md5: list[str] = Field(default_factory=list, description="Extracted MD5 hashes")
    sha1: list[str] = Field(default_factory=list, description="Extracted SHA1 hashes")
    sha256: list[str] = Field(default_factory=list, description="Extracted SHA256 hashes")
    urls: list[str] = Field(default_factory=list, description="Extracted URLs")
    domains: list[str] = Field(default_factory=list, description="Extracted domains")
    emails: list[str] = Field(default_factory=list, description="Extracted email addresses")
    cves: list[str] = Field(default_factory=list, description="Extracted CVE identifiers")
    statistics: IOCStatistics = Field(..., description="Extraction statistics")


class ExtractionErrorResponse(BaseModel):
    """Error response schema for extraction operations"""
    error: str = Field(..., description="Error message")
    details: str | None = Field(None, description="Additional error details")
    file_info: dict[str, Any] | None = Field(None, description="File information if applicable")


class FileUploadInfo(BaseModel):
    """Information about uploaded file"""
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME content type")
    size: int = Field(..., description="File size in bytes")
    encoding_used: str | None = Field(None, description="Character encoding used to decode file")
