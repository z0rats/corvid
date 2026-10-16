import datetime

from sqlalchemy import JSON, DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class ImageGeolocationSearch(Base):
    """A single AI photo-geolocation analysis, saved once the model has responded.

    `result` holds the full analysis (the shape of `ImageGeolocationAnalysis`: the model's
    candidates/clues/caveats/visible text plus the computed text signals and cross-checked
    reference countries); `top_candidate`/`top_confidence` are denormalized
    from `result.candidates[0]` so the history list can render without parsing JSON.
    """

    __tablename__ = "image_geolocation_searches"

    id: Mapped[int] = mapped_column(primary_key=True, comment="Surrogate primary key")
    filename: Mapped[str] = mapped_column(String(500), comment="Original uploaded filename")
    image_sha256: Mapped[str] = mapped_column(
        String(64), index=True, comment="SHA256 of the analyzed image content"
    )
    model_used: Mapped[str] = mapped_column(
        String(200), comment="ID of the LLM model that produced this analysis"
    )
    top_candidate: Mapped[str | None] = mapped_column(
        String(500), comment="Location of the top-ranked candidate, if any"
    )
    top_confidence: Mapped[float | None] = mapped_column(
        Float, comment="Confidence of the top-ranked candidate, if any"
    )
    result: Mapped[dict] = mapped_column(
        JSON, comment="Full analysis payload (ImageGeolocationAnalysis)"
    )
    searched_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="When the analysis ran"
    )
