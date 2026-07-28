from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.core.database import Base
from app.core.models.mixins import TimestampMixin


class Keyword(Base, TimestampMixin):
    """Keyword model for storing user-defined keywords"""
    __tablename__ = 'keywords'

    id: Mapped[int] = mapped_column(primary_key=True, comment="Surrogate primary key")
    keyword: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, comment="Watched keyword, lowercased/stripped by validate_keyword"
    )

    @validates('keyword')
    def validate_keyword(self, key: str, keyword: str) -> str:
        if not keyword or not keyword.strip():
            raise ValueError("Keyword cannot be empty")
        if len(keyword.strip()) > 100:
            raise ValueError("Keyword cannot exceed 100 characters")
        return keyword.strip().lower()

    def __repr__(self) -> str:
        return f"<Keyword(id={self.id}, keyword='{self.keyword}')>"

    def __str__(self) -> str:
        return self.keyword
