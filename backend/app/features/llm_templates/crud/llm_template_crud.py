import logging

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.llm_templates.constants import DEFAULT_CATEGORY_ID
from app.features.llm_templates.models.llm_template_models import AITemplate
from app.features.llm_templates.schemas.llm_template_schemas import AITemplateCreate, AITemplateUpdate

logger = logging.getLogger(__name__)


async def get_template_by_id(db: AsyncSession, template_id: str) -> AITemplate | None:
    """Retrieve a single AI template by ID."""
    stmt = select(AITemplate).where(AITemplate.id == template_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_templates_with_pagination(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    user_id: str | None = None
) -> list[AITemplate]:
    """Retrieve multiple AI templates with pagination and user filtering."""
    stmt = select(AITemplate)

    if user_id:
        stmt = stmt.where(
            (AITemplate.user_id == user_id) | (AITemplate.is_public == True)
        )

    stmt = stmt.order_by(AITemplate.order_number.asc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    templates = list(result.scalars().all())

    logger.info("Retrieved %s templates", len(templates))
    return templates


async def create_new_template(
    db: AsyncSession,
    template: AITemplateCreate,
    user_id: str | None = None
) -> AITemplate:
    """Create a new AI template."""
    logger.info("Creating new template: %s", template.title)

    template_data = template.model_dump()
    if not template_data.get("category_id"):
        template_data["category_id"] = DEFAULT_CATEGORY_ID

    db_template = AITemplate(
        **template_data,
        user_id=user_id
    )

    db.add(db_template)
    await db.flush()
    await db.refresh(db_template)

    logger.info("Template created successfully with ID: %s", db_template.id)
    return db_template


async def update_existing_template(
    db: AsyncSession,
    template_id: str,
    template_update: AITemplateUpdate
) -> AITemplate | None:
    """Update an existing AI template."""
    logger.info("Updating template: %s", template_id)

    db_template = await get_template_by_id(db, template_id)
    if not db_template:
        logger.warning("Template not found for update: %s", template_id)
        return None

    update_data = template_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_template, key, value)

    await db.flush()
    await db.refresh(db_template)

    logger.info("Template updated successfully: %s", template_id)
    return db_template


async def delete_template_by_id(db: AsyncSession, template_id: str) -> bool:
    """Delete an AI template."""
    logger.info("Deleting template: %s", template_id)

    template = await get_template_by_id(db, template_id)
    if not template:
        logger.warning("Template not found for deletion: %s", template_id)
        return False

    await db.delete(template)
    await db.flush()

    logger.info("Template deleted successfully: %s", template_id)
    return True


async def reorder_templates_by_ids(
    db: AsyncSession,
    template_ids: list[str],
    start_order: int = 10,
    increment: int = 10
) -> list[AITemplate]:
    """Reorder templates by assigning new order numbers using a single bulk query."""
    logger.info("Reordering %s templates", len(template_ids))

    stmt = select(AITemplate).where(AITemplate.id.in_(template_ids))
    result = await db.execute(stmt)
    templates_by_id = {t.id: t for t in result.scalars().all()}

    updated_templates = []
    current_order = start_order

    for template_id in template_ids:
        template = templates_by_id.get(template_id)
        if template:
            template.order_number = current_order
            updated_templates.append(template)
            current_order += increment
        else:
            logger.warning("Template not found during reorder: %s", template_id)

    await db.flush()

    logger.info("Successfully reordered %s templates", len(updated_templates))
    return updated_templates


async def move_templates_to_category(
    db: AsyncSession,
    template_ids: list[str],
    category_id: str,
) -> int:
    """Move templates to a different category."""
    logger.info("Moving %s templates to category %s", len(template_ids), category_id)

    stmt = (
        update(AITemplate)
        .where(AITemplate.id.in_(template_ids))
        .values(category_id=category_id)
    )
    result = await db.execute(stmt)
    await db.flush()

    logger.info("Moved %s templates", result.rowcount)
    return result.rowcount
