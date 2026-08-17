from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.models.mixins import TimestampMixin


class ModuleSettings(Base, TimestampMixin):
    __tablename__ = "module_settings"

    name: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
        comment=(
            "Module identifier; 100 matches MODULE_NAME_MAX_LENGTH in config/default_settings.py"
        ),
    )
    enabled: Mapped[bool] = mapped_column(
        default=True, comment="Whether this module is enabled and visible in the UI"
    )
