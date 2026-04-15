import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings.api_keys.config.create_defaults import add_default_api_keys
from app.core.settings.general.crud.general_settings_crud import create_general_settings, get_first_general_settings
from app.core.settings.modules.crud.modules_settings_crud import create_module_setting, module_setting_exists
from app.features.llm_templates.constants import DEFAULT_CATEGORY_ID
from app.features.llm_templates.crud.llm_template_crud import create_new_template
from app.features.llm_templates.crud.template_category_crud import ensure_system_categories_exist
from app.features.llm_templates.models.llm_template_models import AITemplate
from app.features.llm_templates.schemas.llm_template_schemas import AITemplateCreate
from app.features.llm_templates.utils import DEFAULT_TEMPLATES
from app.features.newsfeed.crud.newsfeed_settings_crud import create_newsfeed_setting, get_feed_by_name
from app.features.newsfeed.schemas.newsfeed_schemas import NewsfeedSettingsSchema

logger = logging.getLogger(__name__)


async def create_default_general_settings(db: AsyncSession) -> None:
    """Create default general settings if they don't exist"""
    existing_settings = await get_first_general_settings(db)
    if not existing_settings:
        await create_general_settings(db, darkmode=True)
        logger.info("Created default general settings")


async def create_default_module_settings(db: AsyncSession) -> None:
    """Create default module settings if they don't exist"""
    default_modules: list[tuple[str, bool]] = [
        ("newsfeed", True),
        ("ioc_tools", True),
        ("email_analyzer", True),
        ("domain_finder", True),
        ("llm_templates", True),
        ("cvss_calculator", True),
        ("rule_creator", True)
    ]

    for name, enabled in default_modules:
        if not await module_setting_exists(db, name):
            create_module_setting(db, name, enabled)

    logger.info("Default module settings checked and created")


async def create_default_newsfeeds(db: AsyncSession) -> None:
    """Create default newsfeeds if they don't exist (favicons are fetched in background)"""
    from app.features.newsfeed.utils.default_rss_feeds import DEFAULT_NEWSFEEDS

    for feed_data in DEFAULT_NEWSFEEDS:
        if not await get_feed_by_name(db, feed_data["name"]):
            feed_schema = NewsfeedSettingsSchema(
                name=feed_data["name"],
                url=feed_data["url"],
            )
            await create_newsfeed_setting(db, feed_schema)

    logger.info("Default newsfeeds initialized")


async def create_default_llm_templates(db: AsyncSession) -> None:
    """Create default LLM templates if none exist, ensuring system categories are present."""
    await ensure_system_categories_exist(db)

    result = await db.execute(select(AITemplate).limit(1))
    if result.scalar_one_or_none():
        logger.info("Templates already exist, skipping creation")
        return

    logger.info("No existing templates found. Creating default templates...")
    for template_data in DEFAULT_TEMPLATES:
        data = {**template_data, "category_id": DEFAULT_CATEGORY_ID}
        await create_new_template(db, AITemplateCreate(**data))

    logger.info("Default templates created successfully")


async def initialize_application_defaults(db: AsyncSession) -> None:
    """Initialize all default application settings sequentially"""
    try:
        await create_default_general_settings(db)
        await create_default_module_settings(db)
        await create_default_newsfeeds(db)
        await create_default_llm_templates(db)
        await add_default_api_keys(db)
        logger.info("All default settings initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize application defaults: %s", e)
        raise
