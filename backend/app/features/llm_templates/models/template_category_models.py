import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Boolean, DateTime, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TemplateCategory(Base):
    """Group model for organizing AI templates."""

    __tablename__ = "template_categories"

    id: Mapped[str] = mapped_column(
        String, primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Unique identifier for the category"
    )
    name: Mapped[str] = mapped_column(
        String(100),
        comment="Display name of the category"
    )
    order_number: Mapped[int] = mapped_column(
        Integer, default=0,
        comment="Display order for category listing"
    )
    is_system: Mapped[bool] = mapped_column(
        Boolean, default=False,
        comment="Whether this is a system category that cannot be deleted or renamed"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("(CURRENT_TIMESTAMP)"),
        comment="Timestamp when the category was created"
    )

    def __repr__(self) -> str:
        return f"<TemplateCategory(id='{self.id}', name='{self.name}', system={self.is_system})>"
