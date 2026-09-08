from pydantic import BaseModel, ConfigDict, Field


class TelegramSettingsResponse(BaseModel):
    """Response schema for Telegram notification settings."""

    id: int = Field(..., description="Settings record ID")
    bot_token: str = Field(default="", max_length=500, description="Telegram bot token")
    chat_id: str = Field(default="", max_length=100, description="Telegram chat ID to notify")
    enabled: bool = Field(..., description="Master switch for Telegram delivery")
    notify_scan_events: bool = Field(
        ..., description="Notify on scan completed/cancelled (failures always notify)"
    )
    notify_job_failures: bool = Field(
        ..., description="Notify when a recurring scheduler job starts/stops failing"
    )
    notify_newsfeed_matches: bool = Field(
        ..., description="Notify when a newsfeed article matches a watchlist keyword"
    )
    bot_commands_enabled: bool = Field(
        ..., description="Allow inbound Telegram bot commands (/lookup, /digest, /help)"
    )
    web_base_url: str = Field(
        default="", max_length=500, description="Base URL used to build /lookup deep links"
    )

    model_config = ConfigDict(from_attributes=True)


class TelegramSettingsUpdate(BaseModel):
    """Schema for updating Telegram notification settings."""

    bot_token: str | None = Field(None, max_length=500, description="Telegram bot token")
    chat_id: str | None = Field(None, max_length=100, description="Telegram chat ID to notify")
    enabled: bool | None = Field(None, description="Master switch for Telegram delivery")
    notify_scan_events: bool | None = Field(None, description="Notify on scan completed/cancelled")
    notify_job_failures: bool | None = Field(
        None, description="Notify on scheduler job failure/recovery"
    )
    notify_newsfeed_matches: bool | None = Field(
        None, description="Notify on newsfeed watchlist keyword matches"
    )
    bot_commands_enabled: bool | None = Field(
        None, description="Allow inbound Telegram bot commands (/lookup, /digest, /help)"
    )
    web_base_url: str | None = Field(
        None, max_length=500, description="Base URL used to build /lookup deep links"
    )


class TelegramTestMessageResponse(BaseModel):
    """Response schema for the Telegram test-message endpoint."""

    sent: bool = Field(..., description="Whether the test message was delivered")
    message: str = Field(..., description="Human-readable outcome")
