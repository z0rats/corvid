from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class AlertCreateSchema(BaseModel):
    """Schema for creating a new alert"""
    module: str = Field(..., description="Module that generated the alert", min_length=1, max_length=100)
    title: str = Field(..., description="Alert title", min_length=1, max_length=200)
    message: str = Field(..., description="Alert message content", min_length=1, max_length=1000)


class AlertUpdateSchema(BaseModel):
    """Schema for updating alert read status"""
    read: bool = Field(..., description="Whether the alert has been read")


class AlertSchema(BaseModel):
    """Complete alert response schema"""
    id: int = Field(..., description="Unique alert identifier")
    module: str = Field(..., description="Module that generated the alert")
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message content")
    read: bool = Field(..., description="Whether the alert has been read")
    timestamp: datetime = Field(..., description="When the alert was created")
    timestamp_read: datetime | None = Field(None, description="When the alert was marked as read")

    model_config = ConfigDict(from_attributes=True)


class AlertBulkActionResponse(BaseModel):
    """Response for bulk alert operations"""
    message: str = Field(..., description="Description of the bulk operation performed")
    count: int = Field(..., description="Number of alerts affected")


class UnreadCountResponse(BaseModel):
    """Response for unread alert count"""
    unread_count: int = Field(..., description="Number of alerts that have not been marked as read")
