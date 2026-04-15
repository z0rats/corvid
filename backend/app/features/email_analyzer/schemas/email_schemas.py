from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field
from enum import Enum


class WarningLevel(str, Enum):
    """Warning severity levels for email analysis."""
    GREEN = "green"
    AMBER = "amber"
    RED = "red"


class EmailWarning(BaseModel):
    """Individual security warning from email analysis."""

    warning_tlp: WarningLevel = Field(
        ...,
        description="Traffic Light Protocol level for the warning"
    )
    warning_title: str = Field(
        ...,
        description="Brief title describing the warning",
        min_length=1,
        max_length=200
    )
    warning_message: str = Field(
        ...,
        description="Detailed warning message",
        min_length=1,
        max_length=1000
    )


class EmailHop(BaseModel):
    """Email routing hop information."""

    number: int = Field(
        ...,
        description="Hop sequence number",
        ge=1
    )
    from_server: str | None = Field(
        default=None,
        description="Source server information",
        alias="from"
    )
    by_server: str | None = Field(
        default=None,
        description="Receiving server information",
        alias="by"
    )
    with_protocol: str | None = Field(
        default=None,
        description="Protocol used for transmission",
        alias="with"
    )
    date: str | None = Field(
        default=None,
        description="Timestamp of the hop"
    )
    parse_error: str | None = Field(
        default=None,
        description="Error message if hop parsing failed"
    )

    model_config = ConfigDict(populate_by_name=True)


class EmailAttachment(BaseModel):
    """Email attachment information with security hashes."""

    filename: str = Field(
        ...,
        description="Attachment filename",
        min_length=1,
        max_length=255
    )
    md5: str = Field(
        ...,
        description="MD5 hash of attachment content",
        pattern=r'^[a-fA-F0-9]{32}$'
    )
    sha1: str = Field(
        ...,
        description="SHA1 hash of attachment content",
        pattern=r'^[a-fA-F0-9]{40}$'
    )
    sha256: str = Field(
        ...,
        description="SHA256 hash of attachment content",
        pattern=r'^[a-fA-F0-9]{64}$'
    )


class EmailHashes(BaseModel):
    """Hash values for the email file."""

    md5: str = Field(
        ...,
        description="MD5 hash of email content",
        pattern=r'^[a-fA-F0-9]{32}$'
    )
    sha1: str = Field(
        ...,
        description="SHA1 hash of email content",
        pattern=r'^[a-fA-F0-9]{40}$'
    )
    sha256: str = Field(
        ...,
        description="SHA256 hash of email content",
        pattern=r'^[a-fA-F0-9]{64}$'
    )


class EmailBasicInfo(BaseModel):
    """Basic email header information."""

    from_address: str | None = Field(
        default=None,
        description="Sender email address",
        alias="from"
    )
    to_address: str | None = Field(
        default=None,
        description="Recipient email address",
        alias="to"
    )
    delivered_to: str | None = Field(
        default=None,
        description="Delivered-To header value"
    )
    rcpt_to: str | None = Field(
        default=None,
        description="RCPT-TO header value"
    )
    cc: str | None = Field(
        default=None,
        description="CC recipients"
    )
    return_path: str | None = Field(
        default=None,
        description="Return-Path header value"
    )
    subject: str | None = Field(
        default=None,
        description="Email subject line"
    )
    date: str | None = Field(
        default=None,
        description="Date header value"
    )
    dkim_signature: str | None = Field(
        default=None,
        description="DKIM signature header",
        alias="dkim-signature"
    )
    domainkey_signature: str | None = Field(
        default=None,
        description="DomainKey signature header",
        alias="domainkey-signature"
    )
    message_id: str | None = Field(
        default=None,
        description="Message-ID header value",
        alias="message-id"
    )

    model_config = ConfigDict(populate_by_name=True)


class EmailAnalysisResponse(BaseModel):
    """Complete email analysis response."""

    basic_info: EmailBasicInfo = Field(
        ...,
        description="Basic email header information"
    )
    headers: list[dict[str, str]] = Field(
        ...,
        description="All email headers as key-value pairs"
    )
    eml_hashes: EmailHashes = Field(
        ...,
        description="Hash values of the email file"
    )
    attachments: list[EmailAttachment] = Field(
        default_factory=list,
        description="List of email attachments with hash information"
    )
    hops: list[EmailHop] = Field(
        default_factory=list,
        description="Email routing path information"
    )
    warnings: list[EmailWarning] = Field(
        default_factory=list,
        description="Security warnings and analysis results"
    )
    urls: list[str] = Field(
        default_factory=list,
        description="URLs extracted from email content"
    )
    message_text: list[str] | str = Field(
        default="",
        description="Email message content (text/html)"
    )
    analysis_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when analysis was performed"
    )
    file_size: int | None = Field(
        default=None,
        description="Size of the uploaded email file in bytes",
        ge=0
    )


class EmailAnalysisError(BaseModel):
    """Error response for email analysis failures."""

    error: str = Field(
        ...,
        description="Error message describing what went wrong"
    )
    status: str = Field(
        default="failed",
        description="Analysis status"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when error occurred"
    )


class EmailHealthResponse(BaseModel):
    """Health check response for the email analyzer service."""
    service: str = Field(..., description="Service name")
    status: str = Field(..., description="Service status")
    endpoints: list[str] = Field(..., description="Available endpoints")
    supported_formats: list[str] = Field(..., description="Supported file extensions")
    max_file_size: str = Field(..., description="Maximum file size")


