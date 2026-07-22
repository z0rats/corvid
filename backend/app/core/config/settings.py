from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings"""
    model_config = SettingsConfigDict(env_prefix="DB_", env_file=".env", env_file_encoding="utf-8")

    url: str = Field(default="sqlite:///./data/corvid.db", description="Database URL")
    echo: bool = Field(default=False, description="Enable SQLAlchemy query logging")
    pool_size: int = Field(
        default=10,
        description=(
            "Database connection pool size. Only applies to non-SQLite URLs (e.g. "
            "postgresql+asyncpg://) - the default SQLite backend uses a single "
            "StaticPool connection and ignores this setting entirely."
        ),
    )
    max_overflow: int = Field(
        default=20,
        description=(
            "Maximum database connection overflow. Only applies to non-SQLite URLs "
            "(e.g. postgresql+asyncpg://) - ignored for the default SQLite backend, "
            "same as pool_size."
        ),
    )
    pool_recycle: int = Field(
        default=3600,
        description=(
            "Connection pool recycle time in seconds. Only applies to non-SQLite "
            "URLs (e.g. postgresql+asyncpg://) - ignored for the default SQLite "
            "backend, same as pool_size."
        ),
    )


class LoggingSettings(BaseSettings):
    """Logging configuration settings"""
    model_config = SettingsConfigDict(env_prefix="LOG_", env_file=".env", env_file_encoding="utf-8")

    level: str = Field(default="INFO", description="Logging level")
    dir: str = Field(default="data/logs", description="Log directory path")
    app_name: str = Field(default="corvid", description="Application name for log files")
    max_file_size: int = Field(default=10 * 1024 * 1024, description="Maximum log file size in bytes")
    backup_count: int = Field(default=5, description="Number of backup log files")
    enable_console: bool = Field(default=True, description="Enable console logging")
    enable_file: bool = Field(default=True, description="Enable file logging")


class APISettings(BaseSettings):
    """API configuration settings"""
    model_config = SettingsConfigDict(env_prefix="API_", env_file=".env", env_file_encoding="utf-8")

    title: str = Field(default="Corvid", description="API title")
    version: str = Field(default="2.0.0", description="Application version")
    description: str = Field(
        default="## Corvid interactive API documentation",
        description="API description"
    )
    debug: bool = Field(default=False, description="Enable debug mode")
    max_request_body_bytes: int = Field(default=50 * 1024 * 1024, description="Maximum request body size in bytes")
    cors_origins: list[str] = Field(default=["http://localhost:3000"], description="CORS allowed origins")
    trusted_hosts: list[str] = Field(default=["localhost", "127.0.0.1"], description="Allowed Host header values")
    access_token: str = Field(
        default="",
        description=(
            "Bearer token required on every /api/* request (and on the alerts WebSocket, "
            "as a query param). If empty, one is auto-generated and persisted to "
            "<data_dir>/.access_token on first startup."
        ),
    )


class SecuritySettings(BaseSettings):
    """Security-related configuration settings"""
    model_config = SettingsConfigDict(env_prefix="SECURITY_", env_file=".env", env_file_encoding="utf-8")

    allow_private_network_targets: bool = Field(
        default=False,
        description=(
            "Allow SSRF-guarded outbound requests (e.g. favicon fetching) to target "
            "private/loopback/link-local addresses. For dev/testing only."
        ),
    )
    encryption_key: str = Field(
        default="",
        description=(
            "Secret used to derive the key that encrypts API keys at rest. "
            "If empty, a key is auto-generated and persisted to <data_dir>/.encryption_key."
        ),
    )


class SchedulerSettings(BaseSettings):
    """Scheduler configuration settings"""
    model_config = SettingsConfigDict(env_prefix="SCHEDULER_", env_file=".env", env_file_encoding="utf-8")

    default_fetch_interval: int = Field(default=30, description="Default news fetch interval in minutes")
    max_job_instances: int = Field(default=1, description="Maximum concurrent instances per job")
    blacklist_refresh_interval_hours: int = Field(default=24, description="Address blacklist refresh interval in hours")


class AppSettings(BaseSettings):
    """Main application settings"""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    environment: str = Field(default="development", description="Application environment")
    data_dir: str = Field(default="data", description="Data directory path")
    static_dir: str = Field(default="app/static", description="Static files directory")
    low_disk_space_threshold_bytes: int = Field(
        default=1 * 1024 ** 3,
        description=(
            "Below this much free space on the data_dir mount, healthcheck/startup "
            "report 'low' disk status instead of 'healthy'. Lower this on deployments "
            "that legitimately run close to the edge (e.g. a small VPS)."
        ),
    )

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    api: APISettings = Field(default_factory=APISettings)
    scheduler: SchedulerSettings = Field(default_factory=SchedulerSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)


@lru_cache
def get_settings() -> AppSettings:
    """Get application settings instance (cached).

    In route handlers, prefer injecting via SettingsDep so that tests can
    override settings with app.dependency_overrides[get_settings].

    The module-level ``settings`` instance below is for middleware, config
    modules, and startup code where dependency injection is not available.
    Overriding get_settings in tests will NOT affect those call sites.
    """
    return AppSettings()


settings = get_settings()
