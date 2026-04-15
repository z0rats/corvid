import uuid
from typing import Any

from sqlalchemy import String, JSON, Integer, Float, Text, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AITemplate(Base):
    """AI Template model for storing LLM prompt templates."""

    __tablename__ = "ai_templates"

    id: Mapped[str] = mapped_column(
        String, primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Unique identifier for the template"
    )
    title: Mapped[str] = mapped_column(
        String(200),
        comment="Human-readable template title"
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        comment="Detailed description of the template's purpose"
    )
    example_input_output: Mapped[str | None] = mapped_column(
        Text,
        comment="Example showing expected input and output format"
    )
    ai_agent_role: Mapped[str] = mapped_column(
        Text,
        comment="System prompt defining the AI agent's role and persona"
    )
    ai_agent_task: Mapped[str] = mapped_column(
        Text,
        comment="Task prompt with instructions for the AI agent"
    )
    payload_fields: Mapped[list[Any]] = mapped_column(
        JSON,
        comment="JSON array defining required input fields for the template"
    )
    static_contexts: Mapped[list[Any] | None] = mapped_column(
        JSON, default=list,
        comment="JSON array of static context information to include in prompts"
    )
    web_contexts: Mapped[list[Any] | None] = mapped_column(
        JSON, default=list,
        comment="JSON array of web URLs to fetch and include as context"
    )
    is_public: Mapped[bool] = mapped_column(
        default=False,
        comment="Whether the template is publicly accessible"
    )
    user_id: Mapped[str | None] = mapped_column(
        String(100),
        comment="ID of the user who created the template"
    )
    order_number: Mapped[int | None] = mapped_column(
        Integer, default=0,
        comment="Display order for template listing"
    )
    temperature: Mapped[float | None] = mapped_column(
        Float, default=0.7,
        comment="LLM temperature setting (0.0-1.0) for response randomness"
    )
    model: Mapped[str | None] = mapped_column(
        String(100), default=None, nullable=True,
        comment="Default LLM model to use for template execution (null = use configured default)"
    )
    category_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("template_categories.id"), nullable=True,
        comment="Category this template belongs to"
    )

    @hybrid_property
    def is_valid(self) -> bool:
        """Check if the template has all required fields for execution."""
        return (
            bool(self.title and self.title.strip()) and
            bool(self.ai_agent_role and self.ai_agent_role.strip()) and
            bool(self.ai_agent_task and self.ai_agent_task.strip()) and
            self.payload_fields is not None
        )

    @hybrid_property
    def has_contexts(self) -> bool:
        """Check if the template has any context configurations."""
        return (
            (self.static_contexts and len(self.static_contexts) > 0) or
            (self.web_contexts and len(self.web_contexts) > 0)
        )

    def get_required_payload_fields(self) -> list:
        """Get list of required payload field names."""
        if not self.payload_fields:
            return []
        try:
            return [
                field.get('name')
                for field in self.payload_fields
                if field.get('required', False) and field.get('name')
            ]
        except (TypeError, AttributeError):
            return []

    def validate_payload_data(self, payload_data: dict) -> tuple[bool, list]:
        """Validate provided payload data against template requirements."""
        required_fields = self.get_required_payload_fields()
        provided_fields = set(payload_data.keys()) if payload_data else set()
        missing_fields = [
            field for field in required_fields
            if field not in provided_fields or not payload_data.get(field, '').strip()
        ]
        return len(missing_fields) == 0, missing_fields

    def __repr__(self) -> str:
        return f"<AITemplate(id='{self.id}', title='{self.title}', public={self.is_public})>"

    def __str__(self) -> str:
        return f"AI Template: {self.title} ({self.id})"
