import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LookupResultCreate(BaseModel):
    """A single service's result to persist, as gathered by the frontend"""

    service_key: str = Field(..., description="Key of the service that produced this result")
    service_name: str = Field(..., description="Display name of the service")
    status: str = Field(..., description="found, not_found, or error")
    summary: str = Field(..., description="Short human-readable summary of the result")
    tlp: str = Field(..., description="TLP color assigned to the result")
    data: dict[str, Any] | None = Field(default=None, description="Raw service response, if any")


class SearchCreate(BaseModel):
    """Request to save a completed single-IOC lookup search"""

    ioc: str = Field(..., description="The IOC value that was searched", min_length=1, max_length=2000)
    ioc_type: str = Field(..., description="The detected IOC type", min_length=1, max_length=20)
    results: list[LookupResultCreate] = Field(..., description="Per-service results gathered for this search")


class LookupResultSchema(BaseModel):
    """A single persisted service result"""

    service_key: str
    service_name: str
    status: str
    summary: str
    tlp: str
    data: dict[str, Any] | None = None

    model_config = ConfigDict(from_attributes=True)


class SearchSummary(BaseModel):
    """Summary of a past search run, without its per-service results"""

    id: int = Field(..., description="Search run ID")
    ioc: str = Field(..., description="IOC value that was searched")
    ioc_type: str = Field(..., description="Detected IOC type")
    searched_at: datetime.datetime = Field(..., description="When the search was run")

    model_config = ConfigDict(from_attributes=True)


class SearchDetail(SearchSummary):
    """Full detail of a search run, including its per-service results"""

    results: list[LookupResultSchema] = Field(default_factory=list, description="Per-service results")
