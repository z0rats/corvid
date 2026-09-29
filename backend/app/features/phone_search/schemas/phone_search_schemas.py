import datetime
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

# E.164: a leading '+', then 8-15 digits, the first of which is 1-9 (no leading zero).
_E164_RE = re.compile(r"^\+[1-9]\d{7,14}$")


class ScanRequest(BaseModel):
    """Request to start a new phone number search"""

    phone_number: str = Field(
        ...,
        description="Phone number to search for, in E.164 format (e.g. +15551234567)",
        min_length=8,
        max_length=20,
    )

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        phone_number = v.strip()
        if not _E164_RE.match(phone_number):
            raise ValueError(
                "Phone number must be in E.164 format, e.g. +15551234567 "
                "(leading '+' followed by 8-15 digits)"
            )
        return phone_number


class ProviderResultSchema(BaseModel):
    """A single provider where the searched phone number was found registered"""

    provider_name: str = Field(
        ..., description="Name of the provider where the phone number was found registered"
    )
    extra: dict | None = Field(default=None, description="Provider-specific extra details")

    model_config = ConfigDict(from_attributes=True)


class SearchRunSummary(BaseModel):
    """Summary of a past or in-progress search run, without full provider results"""

    id: int = Field(..., description="Search run ID")
    phone_number: str = Field(..., description="Phone number that was searched")
    status: str = Field(..., description="running, completed, cancelled, or failed")
    total_providers_checked: int = Field(..., description="Number of providers checked")
    found_count: int = Field(
        ..., description="Number of providers where the number was found registered"
    )
    error_message: str | None = Field(default=None, description="Error message if the run failed")
    started_at: datetime.datetime = Field(..., description="When the search started")
    completed_at: datetime.datetime | None = Field(
        default=None, description="When the search completed"
    )

    model_config = ConfigDict(from_attributes=True)


class SearchRunDetail(SearchRunSummary):
    """Full detail of a search run, including its found-provider results"""

    provider_results: list[ProviderResultSchema] = Field(
        default_factory=list, description="Found providers"
    )


class PhoneSearchInfo(BaseModel):
    """Info about the phone search feature's currently active providers"""

    provider_count: int = Field(..., description="Number of provider checkers currently active")
    providers: list[str] = Field(..., description="Names of the currently active providers")
