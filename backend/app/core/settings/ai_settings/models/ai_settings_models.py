from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.models.mixins import TimestampMixin
from app.core.settings.ai_settings.config.default_settings import DEFAULT_MODEL


class AISettings(Base, TimestampMixin):
    """Database model for AI / LLM default model settings (singleton)"""
    __tablename__ = "ai_settings"

    id: Mapped[int] = mapped_column(primary_key=True, comment="Singleton row id, always 1")
    default_model: Mapped[str] = mapped_column(
        String(80), default=DEFAULT_MODEL, comment="Fallback LLM model id used when a feature has no override set"
    )
    newsfeed_analysis_model: Mapped[str | None] = mapped_column(
        String(80), nullable=True, default=None,
        comment="LLM model override for newsfeed article analysis; null = use default_model",
    )
    newsfeed_report_model: Mapped[str | None] = mapped_column(
        String(80), nullable=True, default=None,
        comment="LLM model override for newsfeed report generation; null = use default_model",
    )
    email_analyzer_model: Mapped[str | None] = mapped_column(
        String(80), nullable=True, default=None,
        comment="LLM model override for email search analysis; null = use default_model",
    )
    llm_templates_model: Mapped[str | None] = mapped_column(
        String(80), nullable=True, default=None,
        comment="LLM model override for AI template execution; null = use default_model",
    )
