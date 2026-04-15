import logging

from fastapi import APIRouter, HTTPException, Query, Request, status

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import ReadSessionDep, SessionDep
from app.features.llm_templates.crud.llm_template_crud import (
    get_templates_with_pagination,
    create_new_template,
    update_existing_template,
    delete_template_by_id,
    get_template_by_id,
    reorder_templates_by_ids,
)
from app.features.llm_templates.schemas.llm_template_schemas import (
    AITemplate, AITemplateCreate, AITemplateUpdate, AITemplateExecute,
    TemplateOrderUpdate, PromptEngineerRequest, PromptEngineerResponse,
    StatusMessageResponse, TemplateExecutionResponse, ReorderResponse,
)
from app.features.llm_templates.service.template_management_service import (
    run_engineer_prompt,
    run_execute_template,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai-templates", tags=["AI Templates"])


@router.post(
    "",
    response_model=AITemplate,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
    summary="Create template",
    description="Create a new AI template with role, task, payload fields, and context configuration",
)
async def create_template(template: AITemplateCreate, db: SessionDep) -> AITemplate:
    """Create a new AI template"""
    logger.info("Creating new template: %s", template.title)
    result = await create_new_template(db, template)
    logger.info("Template created successfully: %s", result.id)
    return result


@router.get(
    "",
    response_model=list[AITemplate],
    response_model_exclude_none=True,
    summary="List templates",
    description="Retrieve all accessible AI templates with pagination support",
)
async def get_templates(
    db: ReadSessionDep,
    skip: int = Query(default=0, ge=0, description="Number of templates to skip"),
    limit: int = Query(default=100, ge=1, le=500, description="Maximum number of templates to return"),
    user_id: str | None = None,
) -> list[AITemplate]:
    """Get all accessible templates with pagination"""
    logger.debug("Retrieving templates: skip=%d, limit=%d", skip, limit)
    templates = await get_templates_with_pagination(db, skip, limit, user_id)
    logger.info("Retrieved %d templates", len(templates))
    return templates


@router.get(
    "/{template_id}",
    response_model=AITemplate,
    response_model_exclude_none=True,
    summary="Get template",
    description="Retrieve a specific AI template by its ID",
    responses={404: {"description": "Template not found"}},
)
async def get_template(template_id: str, db: ReadSessionDep) -> AITemplate:
    """Get a specific template by ID"""
    logger.debug("Retrieving template: %s", template_id)
    template = await get_template_by_id(db, template_id)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return template


@router.put(
    "/{template_id}",
    response_model=AITemplate,
    response_model_exclude_none=True,
    summary="Update template",
    description="Update an existing AI template by its ID",
    responses={404: {"description": "Template not found"}},
)
async def update_template(template_id: str, template_update: AITemplateUpdate, db: SessionDep) -> AITemplate:
    """Update an existing template"""
    logger.info("Updating template: %s", template_id)
    template = await update_existing_template(db, template_id, template_update)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    logger.info("Template updated successfully: %s", template_id)
    return template


@router.delete(
    "/{template_id}",
    response_model=StatusMessageResponse,
    summary="Delete template",
    description="Permanently delete an AI template by its ID",
    responses={404: {"description": "Template not found"}},
)
async def delete_template(template_id: str, db: SessionDep) -> StatusMessageResponse:
    """Delete a template"""
    logger.info("Deleting template: %s", template_id)
    success = await delete_template_by_id(db, template_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    logger.info("Template deleted successfully: %s", template_id)
    return StatusMessageResponse(status="success", message="Template deleted successfully")


@router.post(
    "/prompt-engineer",
    response_model=PromptEngineerResponse,
    summary="Engineer prompt",
    description="Generate an optimized prompt configuration from a title and description using an LLM",
    responses={422: {"description": "Prompt engineering failed"}},
)
@limiter.limit("10/minute")
async def engineer_prompt(request: Request, prompt_request: PromptEngineerRequest, db: SessionDep) -> PromptEngineerResponse:
    """Generate prompt configuration based on title and description"""
    logger.info("Engineering prompt for: %s", prompt_request.title)
    try:
        result = await run_engineer_prompt(prompt_request.title, prompt_request.description, prompt_request.model_id, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    logger.info("Prompt engineering completed successfully")
    return result


@router.post(
    "/reorder",
    response_model=ReorderResponse,
    summary="Reorder templates",
    description="Update the display order of templates by providing an ordered list of template IDs",
)
async def reorder_templates(order_update: TemplateOrderUpdate, db: SessionDep) -> ReorderResponse:
    """Update the display order of templates"""
    logger.info("Reordering %d templates", len(order_update.template_ids))
    updated_templates = await reorder_templates_by_ids(db, order_update.template_ids)
    logger.info("Successfully reordered %d templates", len(updated_templates))
    return ReorderResponse(
        status="success",
        updated_count=len(updated_templates),
        message=f"Successfully reordered {len(updated_templates)} templates",
    )


@router.post(
    "/execute/{template_id}",
    response_model=TemplateExecutionResponse,
    summary="Execute template",
    description="Execute an AI template with provided payload data and return the LLM response",
    responses={
        404: {"description": "Template not found"},
        422: {"description": "Template execution failed"},
    },
)
@limiter.limit("10/minute")
async def execute_template(request: Request, template_id: str, execution_data: AITemplateExecute, db: SessionDep) -> TemplateExecutionResponse:
    """Execute an AI template with provided payload data"""
    logger.info("Executing template: %s", template_id)
    template = await get_template_by_id(db, template_id)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    try:
        result = await run_execute_template(template, execution_data, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    logger.info("Template executed successfully: %s", template_id)
    return TemplateExecutionResponse(result=result)
