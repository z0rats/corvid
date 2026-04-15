from pydantic import BaseModel, Field, field_validator
from enum import Enum


class DefangOperation(str, Enum):
    """Supported defang operations"""
    DEFANG = "defang"
    FANG = "fang"


class DefangRequest(BaseModel):
    """Request schema for IOC defanging operations"""
    text: str = Field(..., description="Text containing IOCs to process", min_length=1)
    operation: DefangOperation = Field(
        default=DefangOperation.DEFANG,
        description="Operation to perform: 'defang' or 'fang'"
    )

    @field_validator('text')
    @classmethod
    def validate_text_not_empty(cls, v: str) -> str:
        """Ensure text is not just whitespace"""
        if not v.strip():
            raise ValueError("Text cannot be empty or contain only whitespace")
        return v.strip()


class ProcessedIOC(BaseModel):
    """Schema for a single processed IOC result"""
    original: str = Field(..., description="Original IOC value")
    processed: str = Field(..., description="Processed IOC value")
    types: list[str] = Field(..., description="Detected IOC types")
    changed: bool = Field(..., description="Whether the IOC was modified")


class DefangResponse(BaseModel):
    """Response schema for defang operations"""
    results: list[ProcessedIOC] = Field(..., description="List of processed IOCs")
    total_processed: int = Field(..., description="Total number of IOCs processed")
    total_changed: int = Field(..., description="Number of IOCs that were modified")


class DefangErrorResponse(BaseModel):
    """Error response schema for defang operations"""
    error: str = Field(..., description="Error message")
    details: str | None = Field(None, description="Additional error details")
