import datetime

from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, validates
from sqlalchemy.sql import func

from app.core.database import Base


class Apikey(Base):
    """API key model for storing external service credentials."""

    __tablename__ = "apikeys"

    name: Mapped[str] = mapped_column(
        String(100), primary_key=True,
        comment="Unique name of the API key provider"
    )
    key: Mapped[str] = mapped_column(
        String(500), default="",
        comment="The API key value"
    )
    is_active: Mapped[bool] = mapped_column(
        default=False,
        comment="Whether the key is active for use"
    )
    bulk_ioc_lookup: Mapped[bool] = mapped_column(
        default=False,
        comment="Whether bulk lookup is enabled"
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        comment="Timestamp when the key was created"
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
        comment="Timestamp when the key was last updated"
    )

    @validates('name')
    def validate_name(self, key: str, name: str) -> str:
        if not name or not name.strip():
            raise ValueError("API key name cannot be empty")
        normalized_name = name.strip().lower()
        if len(normalized_name) > 100:
            raise ValueError("API key name cannot exceed 100 characters")
        return normalized_name

    @validates('key')
    def validate_key(self, key: str, api_key: str) -> str:
        if api_key is None:
            return ""
        normalized_key = api_key.strip()
        if len(normalized_key) > 500:
            raise ValueError("API key cannot exceed 500 characters")
        return normalized_key

    def is_configured(self) -> bool:
        """Check if the API key has a non-empty value."""
        return bool(self.key and self.key.strip())

    def is_usable(self) -> bool:
        """Check if the API key is configured and active."""
        return self.is_configured() and self.is_active

    def __repr__(self) -> str:
        status = "active" if self.is_active else "inactive"
        configured = "configured" if self.is_configured() else "not configured"
        return f"<Apikey(name='{self.name}', status='{status}', {configured})>"

    def __str__(self) -> str:
        return f"API Key: {self.name} ({'active' if self.is_active else 'inactive'})"
