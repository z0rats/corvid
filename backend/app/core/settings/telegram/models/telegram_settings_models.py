from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.models.mixins import TimestampMixin
from app.core.security.secrets_crypto import EncryptedString


class TelegramSettings(Base, TimestampMixin):
    """Database model for Telegram bot notification delivery settings (singleton)."""

    __tablename__ = "telegram_settings"

    id: Mapped[int] = mapped_column(primary_key=True, comment="Singleton row id, always 1")
    bot_token: Mapped[str] = mapped_column(
        EncryptedString,
        default="",
        comment="Telegram bot token from @BotFather (encrypted at rest)",
    )
    chat_id: Mapped[str] = mapped_column(
        String(100), default="", comment="Telegram chat ID notifications are sent to"
    )
    enabled: Mapped[bool] = mapped_column(
        default=False, comment="Master switch for Telegram delivery"
    )
    notify_scan_events: Mapped[bool] = mapped_column(
        default=True,
        comment="Notify on scan completed/cancelled (failures always notify while enabled)",
    )
    notify_job_failures: Mapped[bool] = mapped_column(
        default=True,
        comment="Notify when a recurring scheduler job starts or stops failing",
    )
    notify_newsfeed_matches: Mapped[bool] = mapped_column(
        default=True,
        comment="Notify when a newsfeed article matches a watchlist keyword",
    )
    bot_commands_enabled: Mapped[bool] = mapped_column(
        default=False,
        comment="Allow inbound Telegram bot commands (/lookup, /digest, /help). Off by "
        "default: a different trust boundary than outbound pushes, since the bot now acts "
        "on messages (see docs/adr/0012-telegram-bot-polling.md).",
    )
    web_base_url: Mapped[str] = mapped_column(
        String(500),
        default="",
        comment="Externally-reachable base URL of this Corvid instance, used only to build "
        "the /lookup command's web-UI deep link (Corvid has no public URL by default)",
    )

    def is_configured(self) -> bool:
        """Whether both a bot token and chat ID are set."""
        return bool(self.bot_token.strip() and self.chat_id.strip())

    def is_usable(self) -> bool:
        """Whether Telegram delivery is enabled and fully configured."""
        return self.enabled and self.is_configured()
