from typing import Any, Awaitable, Callable, TypeVar

from pydantic import BaseModel
from fastapi import APIRouter

from app.core.dependencies import ReadSessionDep, SessionDep

ResponseT = TypeVar("ResponseT", bound=BaseModel)
UpdateT = TypeVar("UpdateT", bound=BaseModel)


def build_singleton_settings_router(
    *,
    prefix: str,
    tags: list[str],
    response_schema: type[ResponseT],
    update_schema: type[UpdateT],
    get_service: Callable[[Any], Awaitable[Any]],
    update_service: Callable[[Any, UpdateT], Awaitable[Any]],
    on_after_update: Callable[[UpdateT, Any], None] | None = None,
    exclude_none: bool = False,
) -> APIRouter:
    """GET/PUT pair over a single-row settings config.

    `get_service`/`update_service` may return either an ORM row or an
    already-validated `response_schema` instance - `response_schema.model_validate(...)`
    is applied uniformly here regardless (pydantic v2 re-validates an
    already-valid instance without error, confirmed against ai_settings_service.py,
    which already does this internally). `on_after_update` runs synchronously
    after `update_service` returns, before the response is built - for
    username_search's conditional `configure_maigret_db_scheduler` and
    newsfeed's unconditional `configure_news_scheduler`.
    """
    router = APIRouter(prefix=prefix, tags=tags)
    kwargs = {"response_model_exclude_none": True} if exclude_none else {}

    @router.get("", response_model=response_schema, **kwargs)
    async def get_settings(db: ReadSessionDep):
        return response_schema.model_validate(await get_service(db))

    @router.put("", response_model=response_schema, **kwargs)
    async def update_settings(payload: update_schema, db: SessionDep):
        result = await update_service(db, payload)
        if on_after_update:
            on_after_update(payload, result)
        return response_schema.model_validate(result)

    return router
