from pydantic import BaseModel, ConfigDict, Field, field_validator


class ModuleSettingsResponse(BaseModel):
    """Response schema for module settings"""
    name: str = Field(..., description="Module name")
    enabled: bool = Field(..., description="Whether the module is enabled")

    model_config = ConfigDict(from_attributes=True)


class ModuleSettingsCreate(BaseModel):
    """Schema for creating new module settings"""
    name: str = Field(..., min_length=1, max_length=100, description="Module name")
    enabled: bool = Field(default=True, description="Whether the module is enabled")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValueError('Module name must be a non-empty string')
        return v.strip().lower()


class ModuleSettingsUpdate(BaseModel):
    """Schema for updating module settings"""
    enabled: bool | None = Field(None, description="Whether the module is enabled")


class ModuleStatusUpdate(BaseModel):
    """Schema for updating only module status"""
    enabled: bool = Field(..., description="Whether the module is enabled")
