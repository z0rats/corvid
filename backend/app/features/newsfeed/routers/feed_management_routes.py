"""Newsfeed feed management routes - add, delete, validate feeds, manage icons"""

import base64
import logging
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse

from app.core.config.settings import settings
from app.core.dependencies import SessionDep
from app.features.newsfeed.crud.newsfeed_settings_crud import (
    create_custom_feed_with_favicon,
    delete_custom_feed,
    get_feed_by_name,
    get_feeds_with_default_icon,
    update_feed_icon,
)
from app.features.newsfeed.service.icon_management_service import (
    sync_article_icons,
    delete_feed_icon as delete_feed_icon_service,
    get_icon_path,
    refetch_feed_favicon,
    remove_existing_icon,
    save_icon,
)
from app.features.newsfeed.schemas.newsfeed_schemas import (
    BulkIconRefetchResponse,
    FeedIconRefetchResult,
    IconRefetchResponse,
    NewsfeedSettingsSchema,
    NewsfeedSettingsCreateSchema,
    FeedValidationResponse,
    IconUploadResponse,
)
from app.features.newsfeed.utils.validation import validate_feed, validate_and_process_icon

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Newsfeed"])

FEED_ICONS_DIR = Path(settings.static_dir) / "feedicons"


def _decode_feed_name(encoded_name: str) -> str:
    """Decode a base64-encoded feed name, raising HTTP 400 on invalid input"""
    try:
        return base64.b64decode(encoded_name).decode("utf-8")
    except Exception as e:
        logger.warning("Failed to decode feed name: %s", e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid feed name encoding")


@router.post(
    "/settings/modules/newsfeed/validation",
    response_model=FeedValidationResponse,
    response_model_exclude_none=True,
    summary="Validate feed URL",
    description="Validate a feed URL to confirm it is reachable and returns a valid RSS or Atom feed",
    responses={400: {"description": "Invalid or unreachable feed URL"}},
)
async def validate_feed_url(feed_data: NewsfeedSettingsCreateSchema) -> FeedValidationResponse:
    """Validate a feed URL before adding it"""
    is_valid, error_msg, feed_info = validate_feed(str(feed_data.url))
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    return FeedValidationResponse(valid=True, feed_info=feed_info)


@router.post(
    "/settings/modules/newsfeed",
    status_code=status.HTTP_201_CREATED,
    response_model=NewsfeedSettingsSchema,
    response_model_exclude_none=True,
    summary="Add feed",
    description="Add a new custom RSS/Atom feed after validation. Automatically attempts to download the feed's favicon.",
    responses={400: {"description": "Invalid feed URL or duplicate feed name"}},
)
async def add_custom_feed(feed_data: NewsfeedSettingsCreateSchema, db: SessionDep) -> NewsfeedSettingsSchema:
    """Add a new custom feed after validation with automatic favicon download"""
    is_valid, error_msg, _ = validate_feed(str(feed_data.url))
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    if await get_feed_by_name(db, feed_data.name):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Feed name already exists")

    return await create_custom_feed_with_favicon(db, NewsfeedSettingsSchema(**feed_data.model_dump()))


@router.put(
    "/settings/modules/newsfeed/{feed_name}/icon",
    response_model=IconUploadResponse,
    summary="Upload feed icon",
    description="Upload and process a custom icon for a feed. The image is resized and stored server-side.",
    responses={
        400: {"description": "Invalid icon file or feed name encoding"},
        404: {"description": "Feed not found"},
        500: {"description": "Failed to save icon"},
    },
)
async def upload_feed_icon(
    feed_name: str,
    db: SessionDep,
    file: UploadFile = File(...),
) -> IconUploadResponse:
    """Upload and process an icon for a feed"""
    decoded_name = _decode_feed_name(feed_name)
    file_content = await file.read()

    is_valid, error_msg, processed_data = validate_and_process_icon(file_content, file.filename)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    processed_image, icon_id = processed_data

    save_success, save_error = await save_icon(processed_image, icon_id)
    if not save_success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=save_error)

    feed = await update_feed_icon(db, decoded_name, icon_id)
    if not feed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feed not found")

    await sync_article_icons(db, decoded_name, icon_id)
    return IconUploadResponse(message="Icon uploaded successfully", icon_id=icon_id)


@router.delete(
    "/settings/modules/newsfeed/{feed_name}/icon",
    response_model=dict[str, str],
    summary="Delete feed icon",
    description="Delete a feed's custom icon and reset it to the default icon",
    responses={404: {"description": "Feed not found"}},
)
async def delete_feed_icon(feed_name: str, db: SessionDep) -> dict[str, str]:
    """Delete a feed's icon and reset it to the default"""
    decoded_name = _decode_feed_name(feed_name)
    success, message = await delete_feed_icon_service(db, decoded_name)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
    return {"message": message}


@router.post(
    "/settings/modules/newsfeed/{feed_name}/icon/refetch",
    response_model=IconRefetchResponse,
    summary="Refetch feed favicon",
    description="Re-download the favicon for a specific feed from its website",
    responses={
        404: {"description": "Feed not found"},
        422: {"description": "Could not download favicon"},
    },
)
async def refetch_feed_favicon_route(feed_name: str, db: SessionDep) -> IconRefetchResponse:
    """Re-download the favicon for a feed"""
    decoded_name = _decode_feed_name(feed_name)
    success, message, icon_id = await refetch_feed_favicon(db, decoded_name)

    if not success and message == "Feed not found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)

    return IconRefetchResponse(
        success=success,
        message=message,
        feed_name=decoded_name,
        icon_id=icon_id,
    )


@router.post(
    "/settings/modules/newsfeed/icons/refetch-missing",
    response_model=BulkIconRefetchResponse,
    summary="Refetch all missing favicons",
    description="Attempt to download favicons for all feeds currently using the default icon",
)
async def refetch_all_missing_favicons(db: SessionDep) -> BulkIconRefetchResponse:
    """Bulk re-download favicons for all feeds with missing icons"""
    feeds = await get_feeds_with_default_icon(db)

    results = []
    succeeded = 0
    for feed in feeds:
        success, message, icon_id = await refetch_feed_favicon(db, feed.name)
        results.append(FeedIconRefetchResult(
            feed_name=feed.name,
            success=success,
            icon_id=icon_id,
            error=None if success else message,
        ))
        if success:
            succeeded += 1

    return BulkIconRefetchResponse(
        total=len(feeds),
        succeeded=succeeded,
        failed=len(feeds) - succeeded,
        results=results,
    )


@router.delete(
    "/settings/modules/newsfeed",
    response_model=dict[str, str],
    summary="Delete feed",
    description="Delete a custom feed and its associated icon by feed name",
    responses={
        404: {"description": "Feed not found"},
        500: {"description": "Failed to delete feed"},
    },
)
async def delete_custom_feed_route(db: SessionDep, feed_name: str = Query(...)) -> dict[str, str]:
    """Delete a custom feed and its icon"""
    feed = await get_feed_by_name(db, feed_name)
    if not feed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feed not found")

    if feed.icon_id and feed.icon != "default.png":
        remove_existing_icon(get_icon_path(feed.icon_id))

    if not await delete_custom_feed(db, feed_name):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete feed")

    return {"message": "Feed deleted successfully"}


@router.get(
    "/feedicons/{icon_name}",
    summary="Serve feed icon",
    description="Serve a feed icon by filename, falling back to the default icon if not found",
    responses={400: {"description": "Invalid icon name"}},
)
async def get_feed_icon(icon_name: str) -> FileResponse:
    """Serve a feed icon by name, falling back to the default icon if not found"""
    icons_base = FEED_ICONS_DIR.resolve()
    icon_name_base = icon_name.rsplit(".png", 1)[0]
    target = (FEED_ICONS_DIR / f"{icon_name_base}.png").resolve()

    if not target.is_relative_to(icons_base):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid icon name")

    return FileResponse(target if target.exists() else FEED_ICONS_DIR / "default.png")
