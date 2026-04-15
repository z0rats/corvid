import logging

from sqlalchemy import select, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.llm_templates.constants import DEFAULT_CATEGORY_ID, SYSTEM_CATEGORY_IDS
from app.features.llm_templates.models.llm_template_models import AITemplate
from app.features.llm_templates.models.template_category_models import TemplateCategory

logger = logging.getLogger(__name__)


async def get_all_categories(db: AsyncSession) -> list[TemplateCategory]:
    """Retrieve all template categories ordered by order_number."""
    stmt = select(TemplateCategory).order_by(TemplateCategory.order_number.asc())
    result = await db.execute(stmt)
    categories = list(result.scalars().all())
    logger.debug("Retrieved %s categories", len(categories))
    return categories


async def get_category_by_id(db: AsyncSession, category_id: str) -> TemplateCategory | None:
    """Retrieve a single template category by ID."""
    stmt = select(TemplateCategory).where(TemplateCategory.id == category_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_category(db: AsyncSession, name: str) -> TemplateCategory:
    """Create a new template category with auto-assigned order number."""
    logger.info("Creating new category: %s", name)

    stmt = select(func.coalesce(func.max(TemplateCategory.order_number), 0))
    result = await db.execute(stmt)
    max_order = result.scalar_one()

    category = TemplateCategory(name=name, order_number=max_order + 10)
    db.add(category)
    await db.flush()
    await db.refresh(category)

    logger.info("Category created with ID: %s", category.id)
    return category


async def update_category_name(db: AsyncSession, category_id: str, new_name: str) -> TemplateCategory | None:
    """Rename a category. System categories cannot be renamed."""
    logger.info("Updating category %s name to: %s", category_id, new_name)

    category = await get_category_by_id(db, category_id)
    if not category:
        logger.warning("Category not found: %s", category_id)
        return None

    if category.is_system:
        raise ValueError("System groups cannot be renamed")

    category.name = new_name
    await db.flush()
    await db.refresh(category)

    logger.info("Category renamed successfully: %s", category_id)
    return category


async def delete_category(db: AsyncSession, category_id: str, action: str) -> bool:
    """Delete a category. System categories cannot be deleted.
    action: 'move_to_default' moves templates to Default, 'delete_templates' deletes them.
    """
    logger.info("Deleting category %s with action: %s", category_id, action)

    category = await get_category_by_id(db, category_id)
    if not category:
        logger.warning("Category not found: %s", category_id)
        return False

    if category.is_system:
        raise ValueError("System groups cannot be deleted")

    if action == "move_to_default":
        stmt = (
            update(AITemplate)
            .where(AITemplate.category_id == category_id)
            .values(category_id=DEFAULT_CATEGORY_ID)
        )
        await db.execute(stmt)
        logger.info("Moved templates from category %s to Default", category_id)
    elif action == "delete_templates":
        stmt = delete(AITemplate).where(AITemplate.category_id == category_id)
        await db.execute(stmt)
        logger.info("Deleted templates from category %s", category_id)

    await db.delete(category)
    await db.flush()

    logger.info("Category deleted successfully: %s", category_id)
    return True


async def reorder_categories(
    db: AsyncSession,
    category_ids: list[str],
    start_order: int = 0,
    increment: int = 10,
) -> list[TemplateCategory]:
    """Reorder categories by assigning new order numbers."""
    logger.info("Reordering %s categories", len(category_ids))

    stmt = select(TemplateCategory).where(TemplateCategory.id.in_(category_ids))
    result = await db.execute(stmt)
    categories_by_id = {c.id: c for c in result.scalars().all()}

    updated = []
    current_order = start_order
    for cid in category_ids:
        category = categories_by_id.get(cid)
        if category:
            category.order_number = current_order
            updated.append(category)
            current_order += increment

    await db.flush()
    logger.info("Successfully reordered %s categories", len(updated))
    return updated


async def ensure_system_categories_exist(db: AsyncSession) -> None:
    """Create system categories if they don't exist (for fresh databases)."""
    from app.features.llm_templates.constants import FAVORITES_CATEGORY_ID

    for cat_id, name, order in [
        (FAVORITES_CATEGORY_ID, "Favorites", 0),
        (DEFAULT_CATEGORY_ID, "Default", 10),
    ]:
        existing = await get_category_by_id(db, cat_id)
        if not existing:
            category = TemplateCategory(id=cat_id, name=name, order_number=order, is_system=True)
            db.add(category)
            logger.info("Created system category: %s", name)

    await db.flush()
