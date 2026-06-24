import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from alembic import context

from app.core.database import engine, Base
from app.core.config.settings import settings

from app.core.alerts.models.alerts_models import Alert 
from app.core.settings.api_keys.models.api_keys_settings_models import Apikey 
from app.core.settings.general.models.general_settings_models import GeneralSettings 
from app.core.settings.modules.models.modules_settings_models import ModuleSettings 
from app.core.settings.keywords.models.keywords_settings_models import Keyword 
from app.core.settings.cti_profile.models.cti_profile_models import CTIProfileSettings 
from app.features.newsfeed.models.newsfeed_models import NewsfeedSettings, NewsArticle, NewsfeedConfig, TrendsBlacklistEntry 
from app.features.llm_templates.models.llm_template_models import AITemplate 
from app.features.llm_templates.models.template_category_models import TemplateCategory
from app.features.ioc_tools.ioc_lookup.single_lookup.models.blacklist_models import BlacklistedAddress

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
