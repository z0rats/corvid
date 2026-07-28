import datetime

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class Alert(Base):
    """Alert model for storing system notifications"""
    __tablename__ = 'alerts'

    id: Mapped[int] = mapped_column(primary_key=True, comment="Surrogate primary key")
    module: Mapped[str] = mapped_column(String(100), index=True, comment="Feature/module that raised this alert")
    title: Mapped[str] = mapped_column(String(200), comment="Short alert headline")
    message: Mapped[str] = mapped_column(String(1000), comment="Full alert body text")
    read: Mapped[bool] = mapped_column(default=False, index=True, comment="Whether the user has dismissed/read this alert")
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="When the alert was raised"
    )
    timestamp_read: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), comment="When the alert was marked as read, if it has been"
    )
