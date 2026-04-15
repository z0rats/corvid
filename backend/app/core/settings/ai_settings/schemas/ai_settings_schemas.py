from pydantic import BaseModel, ConfigDict, Field


class AISettingsResponse(BaseModel):
    """Response schema for AI settings"""
    id: int = Field(..., description="Settings record ID")
    default_model: str = Field(..., description="Global default LLM model ID")
    newsfeed_analysis_model: str | None = Field(None, description="Override model for newsfeed article analysis")
    newsfeed_report_model: str | None = Field(None, description="Override model for newsfeed report generation")
    email_analyzer_model: str | None = Field(None, description="Override model for email AI analysis")
    llm_templates_model: str | None = Field(None, description="Override model for new LLM templates")

    model_config = ConfigDict(from_attributes=True)


class AISettingsUpdate(BaseModel):
    """Schema for updating AI settings"""
    default_model: str | None = Field(None, description="Global default LLM model ID")
    newsfeed_analysis_model: str | None = Field(None, description="Override model for newsfeed article analysis")
    newsfeed_report_model: str | None = Field(None, description="Override model for newsfeed report generation")
    email_analyzer_model: str | None = Field(None, description="Override model for email AI analysis")
    llm_templates_model: str | None = Field(None, description="Override model for new LLM templates")


class AvailableModel(BaseModel):
    """Schema for an available LLM model"""
    id: str = Field(..., description="Model identifier")
    name: str = Field(..., description="Display name")
    provider: str = Field(..., description="Provider name (OpenAI, Anthropic, etc.)")


class AvailableModelsResponse(BaseModel):
    """Response schema for available models endpoint"""
    models: list[AvailableModel] = Field(..., description="List of available LLM models")
