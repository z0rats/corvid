import logging
import logging.handlers
import sys
from pathlib import Path

from .request_id_config import RequestIdLogFilter
from .settings import settings


def create_detailed_formatter() -> logging.Formatter:
    """Create detailed formatter with request ID for log correlation"""
    return logging.Formatter(
        fmt='%(asctime)s [%(levelname)s] [%(request_id)s] %(name)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def get_log_level(level_str: str) -> int:
    """Convert string log level to logging constant"""
    return getattr(logging, level_str.upper(), logging.INFO)


def create_console_handler(log_level: int) -> logging.StreamHandler:
    """Create console logging handler"""
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    handler.setFormatter(create_detailed_formatter())
    handler.addFilter(RequestIdLogFilter())
    return handler


def create_file_handler(log_file: Path, log_level: int, max_bytes: int, backup_count: int) -> logging.handlers.RotatingFileHandler:
    """Create rotating file logging handler"""
    handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    handler.setLevel(log_level)
    handler.setFormatter(create_detailed_formatter())
    handler.addFilter(RequestIdLogFilter())
    return handler


def create_error_handler(log_file: Path, max_bytes: int, backup_count: int) -> logging.handlers.RotatingFileHandler:
    """Create error-only file logging handler"""
    handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    handler.setLevel(logging.ERROR)
    handler.setFormatter(create_detailed_formatter())
    handler.addFilter(RequestIdLogFilter())
    return handler


def configure_third_party_loggers() -> None:
    """Configure third-party library loggers to prevent spam"""
    loggers_to_configure = [
        "uvicorn.access",
        "uvicorn.error",
        "sqlalchemy.engine",
        "httpx",
        "httpcore",
    ]

    for logger_name in loggers_to_configure:
        logger = logging.getLogger(logger_name)
        logger.propagate = False
        if logger_name in ["uvicorn.access"]:
            logger.setLevel(logging.WARNING)


def setup_logging(
    log_level: str | None = None,
    log_dir: str | None = None,
    app_name: str | None = None,
    max_file_size: int | None = None,
    backup_count: int | None = None,
    enable_console: bool | None = None,
    enable_file: bool | None = None
) -> None:
    """Configure centralized logging for the application"""
    config = settings.logging
    log_level = log_level or config.level
    log_dir = log_dir or config.dir
    app_name = app_name or config.app_name
    max_file_size = max_file_size or config.max_file_size
    backup_count = backup_count or config.backup_count
    enable_console = enable_console if enable_console is not None else config.enable_console
    enable_file = enable_file if enable_file is not None else config.enable_file

    numeric_level = get_log_level(log_level)

    if enable_file:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(numeric_level)

    if enable_console:
        root_logger.addHandler(create_console_handler(numeric_level))

    if enable_file:
        log_path = Path(log_dir)
        root_logger.addHandler(create_file_handler(
            log_path / f"{app_name}.log", logging.DEBUG, max_file_size, backup_count
        ))
        root_logger.addHandler(create_error_handler(
            log_path / f"{app_name}_errors.log", max_file_size, backup_count
        ))

    configure_third_party_loggers()

    logger = logging.getLogger(__name__)
    logger.info("Logging configured - Level: %s, Console: %s, File: %s", log_level, enable_console, enable_file)
    if enable_file:
        logger.info("Log files location: %s", Path(log_dir).absolute())
