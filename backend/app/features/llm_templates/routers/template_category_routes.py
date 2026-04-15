import logging

from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import ReadSessionDep, SessionDep
from app.features.llm_templates.crud.template_category_crud import (
    get_all_categories,
    create_category,
    update_category_name,
    delete_category,
    reorder_categories,
)
from app.features.llm_templates.crud.llm_template_crud import move_templates_to_category
from app.features.llm_templates.schemas.llm_template_schemas import (
    TemplateCategoryCreate,
    TemplateCategoryUpdate,
    TemplateCategoryResponse,
    CategoryOrderUpdate,
    CategoryDeleteRequest,
    MoveTemplatesRequest,
    StatusMessageResponse,
    ReorderResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai-templates/groups", tags=["Template Groups"])


@router.get(
    "",
    response_model=list[TemplateCategoryResponse],
    summary="List groups",
    description="Retrieve all template groups ordered by display order",
)
async def list_categories(db: ReadSessionDep) -> list[TemplateCategoryResponse]:
    """Get all template groups."""
    categories = await get_all_categories(db)
    logger.info("Retrieved %d groups", len(categories))
    return categories


@router.post(
    "",
    response_model=TemplateCategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create group",
    description="Create a new template group",
)
async def create_new_category(data: TemplateCategoryCreate, db: SessionDep) -> TemplateCategoryResponse:
    """Create a new template group."""
    logger.info("Creating group: %s", data.name)
    result = await create_category(db, data.name)
    return result


@router.put(
    "/{category_id}",
    response_model=TemplateCategoryResponse,
    summary="Rename group",
    description="Rename a template group. System groups cannot be renamed.",
    responses={400: {"description": "System group"}, 404: {"description": "Group not found"}},
)
async def rename_category(category_id: str, data: TemplateCategoryUpdate, db: SessionDep) -> TemplateCategoryResponse:
    """Rename a template group."""
    logger.info("Renaming group %s to: %s", category_id, data.name)
    try:
        result = await update_category_name(db, category_id, data.name)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    return result


@router.delete(
    "/{category_id}",
    response_model=StatusMessageResponse,
    summary="Delete group",
    description="Delete a group. Choose to move templates to Default or delete them.",
    responses={400: {"description": "System group"}, 404: {"description": "Group not found"}},
)
async def remove_category(category_id: str, data: CategoryDeleteRequest, db: SessionDep) -> StatusMessageResponse:
    """Delete a template group with specified action for its templates."""
    logger.info("Deleting group %s with action: %s", category_id, data.action)
    try:
        success = await delete_category(db, category_id, data.action)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    return StatusMessageResponse(status="success", message="Group deleted successfully")


@router.post(
    "/reorder",
    response_model=ReorderResponse,
    summary="Reorder groups",
    description="Update the display order of groups",
)
async def reorder_all_categories(data: CategoryOrderUpdate, db: SessionDep) -> ReorderResponse:
    """Reorder template groups."""
    logger.info("Reordering %d groups", len(data.category_ids))
    updated = await reorder_categories(db, data.category_ids)
    return ReorderResponse(
        status="success",
        updated_count=len(updated),
        message=f"Successfully reordered {len(updated)} groups",
    )


@router.post(
    "/move-templates",
    response_model=StatusMessageResponse,
    summary="Move templates",
    description="Move templates from one group to another",
)
async def move_templates(data: MoveTemplatesRequest, db: SessionDep) -> StatusMessageResponse:
    """Move templates to a different group."""
    logger.info("Moving %d templates to group %s", len(data.template_ids), data.category_id)
    count = await move_templates_to_category(db, data.template_ids, data.category_id)
    return StatusMessageResponse(status="success", message=f"Moved {count} templates")
