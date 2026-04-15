from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.settings.ai_settings.config.default_settings import DEFAULT_MODEL


class AISettings(Base):
    """Database model for AI / LLM default model settings (singleton)"""
    __tablename__ = "ai_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    default_model: Mapped[str] = mapped_column(String(80), default=DEFAULT_MODEL)
    newsfeed_analysis_model: Mapped[str | None] = mapped_column(String(80), nullable=True, default=None)
    newsfeed_report_model: Mapped[str | None] = mapped_column(String(80), nullable=True, default=None)
    email_analyzer_model: Mapped[str | None] = mapped_column(String(80), nullable=True, default=None)
    llm_templates_model: Mapped[str | None] = mapped_column(String(80), nullable=True, default=None)
