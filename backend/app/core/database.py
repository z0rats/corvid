import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool

from app.core.config.settings import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base class"""
    pass


def _to_async_url(url: str) -> str:
    """Convert a sync database URL to its async driver equivalent"""
    if url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql+psycopg2://"):
        return url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    return url


def create_database_engine() -> AsyncEngine:
    """Create and configure async SQLAlchemy database engine from settings"""
    db_url = _to_async_url(settings.database.url)
    echo = settings.database.echo and settings.environment != "production"

    if echo:
        logger.warning("DB_ECHO is enabled — SQL queries will be logged. Disable in production.")

    if "sqlite" in db_url:
        engine = create_async_engine(
            db_url,
            connect_args={"check_same_thread": False, "timeout": 30},
            echo=echo,
            poolclass=StaticPool,
        )

        @event.listens_for(engine.sync_engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:
            """Enable WAL so readers (e.g. SSE progress polling) aren't blocked by
            the scheduler or an in-progress scan holding a write lock."""
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()
    else:
        engine = create_async_engine(
            db_url,
            echo=echo,
            pool_size=settings.database.pool_size,
            max_overflow=settings.database.max_overflow,
            pool_pre_ping=True,
            pool_recycle=settings.database.pool_recycle,
        )

    logger.info("Async database engine created successfully")
    return engine


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create async session factory for database operations"""
    return async_sessionmaker(engine, expire_on_commit=False)


# Initialize database components
engine = create_database_engine()
AsyncSessionLocal = create_session_factory(engine)


async def dispose_database_engine() -> None:
    """Dispose the database engine and close all pooled connections."""
    await engine.dispose()
    logger.info("Database engine disposed")


@asynccontextmanager
async def managed_session() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager providing a session with automatic commit and cleanup.

    Use this outside of FastAPI's dependency injection (e.g., startup tasks,
    scheduled jobs, health checks) to get the same error-handling behaviour
    as the ``get_db`` dependency.

    Commits on success as a safety net for callers that forget to commit.
    On exception, rolls back and re-raises so the caller can respond.
    """
    async with AsyncSessionLocal() as db:
        try:
            yield db
            await db.commit()
        except Exception:
            await db.rollback()
            raise
