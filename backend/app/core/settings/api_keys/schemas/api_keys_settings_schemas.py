from pydantic import BaseModel, ConfigDict, Field, field_validator


def _strip_required(value: str) -> str:
    """Strip whitespace and raise if the result is empty."""
    stripped = value.strip()
    if not stripped:
        raise ValueError("Value cannot be empty")
    return stripped


class ApikeySchema(BaseModel):
    """Schema for reading an API key entry."""
    name: str = Field(..., min_length=1, max_length=100, description="API key provider name")
    key: str = Field(default="", max_length=500, description="API key string")
    is_active: bool = Field(default=False, description="Whether the key is active")
    bulk_ioc_lookup: bool = Field(default=False, description="Whether bulk lookup is enabled")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        return _strip_required(v)

    @field_validator('key')
    @classmethod
    def validate_key(cls, v: str) -> str:
        return v.strip()

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [{
                "name": "virustotal",
                "key": "your-api-key-here",
                "is_active": True,
                "bulk_ioc_lookup": False
            }]
        },
    )


class ApikeyCreateRequest(BaseModel):
    """Schema for API key creation requests."""
    name: str = Field(..., min_length=1, max_length=100, description="API key provider name")
    key: str = Field(..., min_length=1, max_length=500, description="API key string")
    is_active: bool = Field(default=False, description="Whether the key is active")
    bulk_ioc_lookup: bool = Field(default=False, description="Whether bulk lookup is enabled")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        return _strip_required(v)

    @field_validator('key')
    @classmethod
    def validate_key(cls, v: str) -> str:
        return _strip_required(v)


class ApikeyUpdateRequest(BaseModel):
    """Schema for API key partial update requests."""
    key: str | None = Field(None, max_length=500, description="API key string")
    is_active: bool | None = Field(None, description="Whether the key is active")
    bulk_ioc_lookup: bool | None = Field(None, description="Whether bulk lookup is enabled")

    @field_validator('key')
    @classmethod
    def validate_key(cls, v: str | None) -> str | None:
        return v.strip() if v is not None else v


class UpdateActiveStatusRequest(BaseModel):
    """Request body for updating the is_active flag on an API key"""
    is_active: bool = Field(..., description="Whether the key is active")


class UpdateBulkLookupStatusRequest(BaseModel):
    """Request body for updating the bulk_ioc_lookup flag on an API key"""
    bulk_ioc_lookup: bool = Field(..., description="Whether bulk lookup is enabled")


class DeleteApikeyResponse(BaseModel):
    """Response model for deleting an API key."""
    apikey: ApikeySchema = Field(..., description="Deleted API key data")
    message: str = Field(..., description="Success message")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "apikey": {
                    "name": "virustotal",
                    "key": "",
                    "is_active": False,
                    "bulk_ioc_lookup": False
                },
                "message": "API key deleted successfully"
            }]
        },
    )


class ApikeyStateResponse(BaseModel):
    """Response model for API key active state."""
    name: str = Field(..., description="API key name")
    is_active: bool = Field(..., description="Whether the key is active")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "name": "virustotal",
                "is_active": True
            }]
        },
    )


class ApikeyBulkLookupStateResponse(BaseModel):
    """Response model for API key bulk lookup state."""
    name: str = Field(..., description="API key name")
    bulk_ioc_lookup: bool = Field(..., description="Whether bulk lookup is enabled")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "name": "virustotal",
                "bulk_ioc_lookup": True
            }]
        },
    )


class ApikeyStatusSummary(BaseModel):
    """Summary of API key configuration status."""
    total_keys: int = Field(..., description="Total number of API keys")
    configured_keys: int = Field(..., description="Number of configured keys")
    active_keys: int = Field(..., description="Number of active keys")
    bulk_enabled_keys: int = Field(..., description="Number of bulk-enabled keys")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "total_keys": 25,
                "configured_keys": 8,
                "active_keys": 6,
                "bulk_enabled_keys": 3
            }]
        },
    )
