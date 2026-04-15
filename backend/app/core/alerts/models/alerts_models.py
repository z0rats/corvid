import datetime

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class Alert(Base):
    """Alert model for storing system notifications"""
    __tablename__ = 'alerts'

    id: Mapped[int] = mapped_column(primary_key=True)
    module: Mapped[str] = mapped_column(String(100), index=True)
    title: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(String(1000))
    read: Mapped[bool] = mapped_column(default=False, index=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    timestamp_read: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
