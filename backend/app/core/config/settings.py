import subprocess
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _dev_version() -> str:
    """Best-effort version when API_VERSION isn't set in the environment - local
    dev running outside the release Docker image, which always stamps
    API_VERSION from the git tag at build time (see backend/Dockerfile's
    `ARG VERSION` / `ENV API_VERSION`). Never runs inside that image: the env
    var is always present there, even for an untagged build (falls back to
    "0.0.0-dev" itself)."""
    try:
        result = subprocess.run(
            # --match restricts this to version-shaped tags (v1.2.3) - the repo has at
            # least one stray non-version tag ("push") that --tags alone would happily
            # match instead, since git describe just picks the nearest reachable tag.
            ["git", "describe", "--tags", "--dirty", "--always", "--match", "v[0-9]*"],
            cwd=Path(__file__).resolve().parent,
            capture_output=True,
            text=True,
            timeout=2,
            check=True,
        )
        return result.stdout.strip().removeprefix("v")
    except OSError, subprocess.SubprocessError:
        return "0.0.0-dev"


class DatabaseSettings(BaseSettings):
    """Database configuration settings"""

    model_config = SettingsConfigDict(env_prefix="DB_", env_file=".env", env_file_encoding="utf-8")

    url: str = Field(default="sqlite:///./data/corvid.db", description="Database URL")
    echo: bool = Field(default=False, description="Enable SQLAlchemy query logging")
    pool_size: int = Field(
        default=10,
        description="Database connection pool size, for both SQLite and non-SQLite URLs.",
    )
    max_overflow: int = Field(
        default=20,
        description="Maximum database connection overflow, for both SQLite and non-SQLite URLs.",
    )
    pool_recycle: int = Field(
        default=3600,
        description=(
            "Connection pool recycle time in seconds. Only applies to non-SQLite URLs "
            "(e.g. postgresql+asyncpg://) - ignored for the SQLite backend, whose local "
            "connections don't go stale the way a networked DB's can."
        ),
    )


class LoggingSettings(BaseSettings):
    """Logging configuration settings"""

    model_config = SettingsConfigDict(env_prefix="LOG_", env_file=".env", env_file_encoding="utf-8")

    level: str = Field(default="INFO", description="Logging level")
    dir: str = Field(default="data/logs", description="Log directory path")
    app_name: str = Field(default="corvid", description="Application name for log files")
    max_file_size: int = Field(
        default=10 * 1024 * 1024, description="Maximum log file size in bytes"
    )
    backup_count: int = Field(default=5, description="Number of backup log files")
    enable_console: bool = Field(default=True, description="Enable console logging")
    enable_file: bool = Field(default=True, description="Enable file logging")


class APISettings(BaseSettings):
    """API configuration settings"""

    model_config = SettingsConfigDict(env_prefix="API_", env_file=".env", env_file_encoding="utf-8")

    title: str = Field(default="Corvid", description="API title")
    version: str = Field(default_factory=_dev_version, description="Application version")
    description: str = Field(
        default="## Corvid interactive API documentation", description="API description"
    )
    debug: bool = Field(default=False, description="Enable debug mode")
    max_request_body_bytes: int = Field(
        default=50 * 1024 * 1024, description="Maximum request body size in bytes"
    )
    cors_origins: list[str] = Field(
        default=["http://localhost:3000"], description="CORS allowed origins"
    )
    trusted_hosts: list[str] = Field(
        default=["localhost", "127.0.0.1"], description="Allowed Host header values"
    )
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

    model_config = SettingsConfigDict(
        env_prefix="SECURITY_", env_file=".env", env_file_encoding="utf-8"
    )

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

    model_config = SettingsConfigDict(
        env_prefix="SCHEDULER_", env_file=".env", env_file_encoding="utf-8"
    )

    default_fetch_interval: int = Field(
        default=30, description="Default news fetch interval in minutes"
    )
    max_job_instances: int = Field(default=1, description="Maximum concurrent instances per job")
    blacklist_refresh_interval_hours: int = Field(
        default=24, description="Address blacklist refresh interval in hours"
    )


class LLMSettings(BaseSettings):
    """Local LLM provider configuration settings"""

    model_config = SettingsConfigDict(env_prefix="LLM_", env_file=".env", env_file_encoding="utf-8")

    ollama_base_url: str = Field(
        default="http://localhost:11434/v1",
        description=(
            "Base URL of a local Ollama server's OpenAI-compatible API. Models pulled there "
            "are auto-discovered and offered alongside the cloud providers, with no API key "
            "needed. Running the backend itself via Docker Compose on macOS/Windows (Docker "
            "Desktop)? Point this at http://host.docker.internal:11434/v1 instead - "
            "'localhost' inside the container is the container, not your host machine."
        ),
    )


class AppSettings(BaseSettings):
    """Main application settings"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    environment: str = Field(default="development", description="Application environment")
    data_dir: str = Field(default="data", description="Data directory path")
    static_dir: str = Field(default="app/static", description="Static files directory")
    low_disk_space_threshold_bytes: int = Field(
        default=1 * 1024**3,
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
    llm: LLMSettings = Field(default_factory=LLMSettings)


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
