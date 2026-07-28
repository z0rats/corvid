import asyncio
import importlib
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from alembic import context

from app.core.database import engine, Base
from app.core.config.settings import settings


def _import_all_models() -> None:
    """Import every model module under `app/**/models/` so `Base.metadata` (and
    therefore `alembic revision --autogenerate`) sees all of them.

    This used to be a hand-maintained list of imports that only covered 10 of
    the 27 model classes - `--autogenerate` couldn't see the other 17 and would
    either miss real schema changes for them or propose dropping their tables
    outright, thinking they shouldn't exist. Walking the filesystem instead of
    listing classes means a new feature's models are picked up automatically,
    with no separate list to remember to update. See
    docs/database-schema-audit.md section 6, phase 1 (finding #2).
    """
    backend_dir = Path(__file__).resolve().parent.parent
    app_dir = backend_dir / "app"
    for models_dir in sorted(app_dir.rglob("models")):
        if not models_dir.is_dir():
            continue
        for py_file in sorted(models_dir.glob("*.py")):
            if py_file.stem == "__init__":
                continue
            module_name = ".".join(py_file.relative_to(backend_dir).with_suffix("").parts)
            importlib.import_module(module_name)


_import_all_models()

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Configures the context with just a URL so an Engine is not required.
    Calls to context.execute() emit the given SQL string to the script output.
    """
    url = settings.database.url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """Run migrations against a synchronous connection"""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode using the async application engine."""
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
