import logging
from functools import lru_cache
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, managed_session
from app.core.config.settings import AppSettings, get_settings

logger = logging.getLogger(__name__)


@lru_cache
def _get_database_type() -> str:
    """Get database type from the SQLAlchemy engine dialect (cached)"""
    from app.core.database import engine
    return engine.dialect.name


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for write operations.

    Commits on success so handlers don't need to call commit() themselves.
    On exception, rolls back and re-raises so the global handler can respond.
    """
    async with AsyncSessionLocal() as db:
        try:
            yield db
            await db.commit()
        except Exception:
            await db.rollback()
            raise


async def get_read_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for read-only operations.

    Does NOT auto-commit — avoids unnecessary write transactions for GET endpoints.
    On exception, rolls back and re-raises so the global handler can respond.
    """
    async with AsyncSessionLocal() as db:
        try:
            yield db
        except Exception:
            await db.rollback()
            raise


SessionDep = Annotated[AsyncSession, Depends(get_db)]
ReadSessionDep = Annotated[AsyncSession, Depends(get_read_db)]
SettingsDep = Annotated[AppSettings, Depends(get_settings)]


async def validate_database_connection() -> bool:
    """Validate database connection is working"""
    try:
        async with managed_session() as db:
            await db.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error("Database connection validation failed: %s", e)
        return False


async def get_database_health() -> dict[str, str]:
    """Get database health status information"""
    try:
        is_connected = await validate_database_connection()
        return {
            "status": "healthy" if is_connected else "unhealthy",
            "connection": "active" if is_connected else "failed",
            "database_type": _get_database_type()
        }
    except Exception as e:
        logger.error("Error checking database health: %s", e)
        return {
            "status": "unhealthy",
            "connection": "error",
            "database_type": "unknown",
            "error": str(e)
        }


DatabaseHealthDep = Annotated[dict[str, str], Depends(get_database_health)]

# Reusable query parameter aliases for consistent pagination across all endpoints
SkipQuery = Annotated[int, Query(ge=0, description="Number of items to skip")]
LimitQuery = Annotated[int, Query(ge=1, le=500, description="Maximum number of items to return")]
PageQuery = Annotated[int, Query(ge=1, description="Page number")]
PageSizeQuery = Annotated[int, Query(ge=1, le=100, description="Number of items per page")]
