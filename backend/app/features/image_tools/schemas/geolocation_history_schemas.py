import datetime

from pydantic import BaseModel, ConfigDict, Field

from .image_schemas import ImageGeolocationAIResult


class GeolocationSearchSummary(BaseModel):
    """Summary of a past AI geolocation analysis, without its full clue list."""

    id: int = Field(..., description="History record ID")
    filename: str = Field(..., description="Original uploaded filename")
    model_used: str = Field(..., description="ID of the LLM model used")
    top_candidate: str | None = Field(
        default=None, description="Location of the top-ranked candidate, if any"
    )
    top_confidence: float | None = Field(
        default=None, description="Confidence of the top-ranked candidate, if any"
    )
    searched_at: datetime.datetime = Field(..., description="When the analysis ran")

    model_config = ConfigDict(from_attributes=True)


class GeolocationSearchDetail(GeolocationSearchSummary):
    """Full detail of a past AI geolocation analysis, including its clue list."""

    result: ImageGeolocationAIResult = Field(
        ..., description="Candidates, clues, and caveats produced by the analysis"
    )
