from pydantic import BaseModel, ConfigDict, Field


class PhoneSearchConfigSchema(BaseModel):
    id: int = Field(..., description="Configuration record ID")
    timeout_seconds: int = Field(..., description="Per-provider request timeout in seconds")
    proxy_url: str | None = Field(default=None, description="Proxy URL used for provider checks")

    model_config = ConfigDict(from_attributes=True)


class PhoneSearchConfigUpdateSchema(BaseModel):
    timeout_seconds: int | None = Field(
        default=None, ge=1, le=60, description="Per-provider request timeout in seconds"
    )
    proxy_url: str | None = Field(
        default=None, max_length=500, description="Proxy URL used for provider checks"
    )
