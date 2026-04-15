import json
import logging
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger(__name__)


def _parse_json_list(v: Any, field_name: str) -> list[dict[str, Any]]:
    """Normalise a DB JSON-string or already-parsed list into a list of dicts."""
    if isinstance(v, str):
        try:
            parsed = json.loads(v)
            return parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning("Failed to parse %s: %s", field_name, e)
            return []
    return v or []


class PayloadField(BaseModel):
    """Schema for template payload field definitions."""
    name: str = Field(..., description="Field name", min_length=1, max_length=100)
    description: str = Field(..., description="Field description", max_length=500)
    required: bool = Field(True, description="Whether the field is required")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Field name must contain only alphanumeric characters, hyphens, and underscores')
        return v


class StaticContext(BaseModel):
    """Schema for static context definitions."""
    name: str = Field(..., description="Context name", min_length=1, max_length=200)
    content: str = Field(..., description="Context content", max_length=50000)
    description: str | None = Field(None, description="Context description", max_length=500)


class WebContext(BaseModel):
    """Schema for web context definitions."""
    name: str = Field(..., description="Context name", min_length=1, max_length=200)
    url: str = Field(..., description="URL to fetch content from")
    description: str | None = Field(None, description="Context description", max_length=500)

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class AITemplateBase(BaseModel):
    """Base schema for AI templates."""
    title: str = Field(..., description="Template title", min_length=1, max_length=200)
    description: str | None = Field(None, description="Template description", max_length=1000)
    example_input_output: str | None = Field(None, description="Example usage", max_length=5000)
    ai_agent_role: str = Field(..., description="AI agent role/system prompt", min_length=1, max_length=2000)
    ai_agent_task: str = Field(..., description="AI agent task/user prompt", min_length=1, max_length=5000)
    payload_fields: list[dict[str, Any]] = Field(default_factory=list, description="Template payload fields")
    static_contexts: list[dict[str, Any]] = Field(default_factory=list, description="Static contexts")
    web_contexts: list[dict[str, Any]] = Field(default_factory=list, description="Web contexts")
    is_public: bool = Field(False, description="Whether template is public")
    order_number: int | None = Field(0, description="Display order", ge=0)
    temperature: float | None = Field(0.7, description="LLM temperature", ge=0.0, le=1.0)
    model: str | None = Field(None, description="LLM model to use (null = use configured default)", max_length=100)
    category_id: str | None = Field(None, description="Category this template belongs to")

    @field_validator('payload_fields')
    @classmethod
    def validate_payload_fields(cls, v: list[dict[str, Any]]) -> list[dict[str, Any]]:
        field_names: set[str] = set()
        for field in v:
            if not isinstance(field, dict):
                raise ValueError('Each payload field must be a dictionary')
            if 'name' not in field:
                raise ValueError('Payload field must have a name')
            if 'description' not in field:
                raise ValueError('Payload field must have a description')
            name = field['name']
            if name in field_names:
                raise ValueError(f'Duplicate payload field name: {name}')
            field_names.add(name)
            try:
                PayloadField(**field)
            except Exception as e:
                raise ValueError(f'Invalid payload field "{name}": {e}')
        return v

    @field_validator('static_contexts')
    @classmethod
    def validate_static_contexts(cls, v: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for i, context in enumerate(v or []):
            if not isinstance(context, dict):
                raise ValueError(f'Static context {i} must be a dictionary')
            try:
                StaticContext(**context)
            except Exception as e:
                raise ValueError(f'Invalid static context {i}: {e}')
        return v or []

    @field_validator('web_contexts')
    @classmethod
    def validate_web_contexts(cls, v: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for i, context in enumerate(v or []):
            if not isinstance(context, dict):
                raise ValueError(f'Web context {i} must be a dictionary')
            try:
                WebContext(**context)
            except Exception as e:
                raise ValueError(f'Invalid web context {i}: {e}')
        return v or []

    @field_validator('model')
    @classmethod
    def validate_model(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            return None
        return v.strip() if v else None


class AITemplateCreate(AITemplateBase):
    """Schema for creating AI templates."""
    pass


class AITemplateUpdate(BaseModel):
    """Schema for updating AI templates (all fields optional)."""
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    example_input_output: str | None = Field(None, max_length=5000)
    ai_agent_role: str | None = Field(None, min_length=1, max_length=2000)
    ai_agent_task: str | None = Field(None, min_length=1, max_length=5000)
    payload_fields: list[dict[str, Any]] | None = None
    static_contexts: list[dict[str, Any]] | None = None
    web_contexts: list[dict[str, Any]] | None = None
    is_public: bool | None = None
    order_number: int | None = Field(None, ge=0)
    temperature: float | None = Field(None, ge=0.0, le=1.0)
    model: str | None = Field(None, max_length=100)
    category_id: str | None = None

    @field_validator('payload_fields')
    @classmethod
    def validate_payload_fields(cls, v: list[dict[str, Any]] | None) -> list[dict[str, Any]] | None:
        return AITemplateBase.validate_payload_fields(v) if v is not None else v

    @field_validator('static_contexts')
    @classmethod
    def validate_static_contexts(cls, v: list[dict[str, Any]] | None) -> list[dict[str, Any]] | None:
        return AITemplateBase.validate_static_contexts(v) if v is not None else v

    @field_validator('web_contexts')
    @classmethod
    def validate_web_contexts(cls, v: list[dict[str, Any]] | None) -> list[dict[str, Any]] | None:
        return AITemplateBase.validate_web_contexts(v) if v is not None else v

    @field_validator('model')
    @classmethod
    def validate_model(cls, v: str | None) -> str | None:
        return AITemplateBase.validate_model(v) if v is not None else v


class AITemplate(BaseModel):
    """Schema for AI template responses — normalises DB JSON strings on load."""
    id: str
    title: str
    description: str | None = None
    example_input_output: str | None = None
    ai_agent_role: str
    ai_agent_task: str
    payload_fields: list[dict[str, Any]] = Field(default_factory=list)
    static_contexts: list[dict[str, Any]] = Field(default_factory=list)
    web_contexts: list[dict[str, Any]] = Field(default_factory=list)
    is_public: bool = False
    user_id: str | None = None
    order_number: int | None = 0
    temperature: float | None = 1.0
    model: str | None = None
    category_id: str | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator('payload_fields', mode='before')
    @classmethod
    def parse_payload_fields(cls, v: Any) -> list[dict[str, Any]]:
        return _parse_json_list(v, 'payload_fields')

    @field_validator('static_contexts', mode='before')
    @classmethod
    def parse_static_contexts(cls, v: Any) -> list[dict[str, Any]]:
        return _parse_json_list(v, 'static_contexts')

    @field_validator('web_contexts', mode='before')
    @classmethod
    def parse_web_contexts(cls, v: Any) -> list[dict[str, Any]]:
        return _parse_json_list(v, 'web_contexts')


class AITemplateExecute(BaseModel):
    """Schema for template execution requests."""
    template_id: str = Field(..., description="Template ID to execute")
    payload_data: dict[str, str] = Field(..., description="Payload field values")
    override_temperature: float | None = Field(None, description="Override temperature", ge=0.0, le=1.0)
    override_model: str | None = Field(None, description="Override model", max_length=100)

    @field_validator('payload_data')
    @classmethod
    def validate_payload_data(cls, v: dict[str, str]) -> dict[str, str]:
        for key in v:
            if not key.strip():
                raise ValueError('Payload data keys cannot be empty')
        return v

    @field_validator('override_model')
    @classmethod
    def validate_override_model(cls, v: str | None) -> str | None:
        if v and not v.strip():
            raise ValueError('Override model cannot be empty')
        return v.strip() if v else None


class TemplateOrderUpdate(BaseModel):
    """Schema for template reordering requests."""
    template_ids: list[str] = Field(..., description="Ordered list of template IDs")


class PromptEngineerRequest(BaseModel):
    """Schema for prompt engineering requests."""
    title: str = Field(..., description="Template title", min_length=1, max_length=200)
    description: str = Field(..., description="Template description", min_length=1, max_length=1000)
    model_id: str | None = Field(None, description="Model to use for prompt engineering (null = use configured default)")


class PromptEngineerResponse(BaseModel):
    """Structured response from the prompt engineering endpoint."""
    ai_agent_role: str
    ai_agent_task: str
    payload_fields: list[dict[str, Any]]
    example_input_output: str


class StatusMessageResponse(BaseModel):
    """Response for simple status messages."""
    status: str
    message: str


class TemplateExecutionResponse(BaseModel):
    """Response for template execution."""
    result: str


class ReorderResponse(BaseModel):
    """Response for template reorder operation."""
    status: str
    updated_count: int
    message: str


class TemplateCategoryCreate(BaseModel):
    """Schema for creating a template category."""
    name: str = Field(..., description="Category name", min_length=1, max_length=100)


class TemplateCategoryUpdate(BaseModel):
    """Schema for updating a template category."""
    name: str = Field(..., description="Category name", min_length=1, max_length=100)


class TemplateCategoryResponse(BaseModel):
    """Schema for template category responses."""
    id: str
    name: str
    order_number: int
    is_system: bool

    model_config = ConfigDict(from_attributes=True)


class CategoryOrderUpdate(BaseModel):
    """Schema for category reordering requests."""
    category_ids: list[str] = Field(..., description="Ordered list of category IDs")


class CategoryDeleteRequest(BaseModel):
    """Schema for category deletion with action choice."""
    action: str = Field(..., description="Action for templates: move_to_default or delete_templates", pattern="^(move_to_default|delete_templates)$")


class MoveTemplatesRequest(BaseModel):
    """Schema for moving templates between categories."""
    template_ids: list[str] = Field(..., description="Template IDs to move")
    category_id: str = Field(..., description="Target category ID")
