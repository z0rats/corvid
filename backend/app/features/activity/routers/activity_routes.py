from typing import Annotated

from fastapi import APIRouter, Query

from app.core.dependencies import ReadSessionDep

from ..schemas.activity_schemas import ActivityItem
from ..service.activity_service import list_recent_activity

router = APIRouter(prefix="/api/activity", tags=["Activity"])


@router.get(
    "",
    response_model=list[ActivityItem],
    summary="Recent activity",
    description="The newest runs/lookups across every feature with a saved history, newest first",
)
async def get_recent_activity(
    db: ReadSessionDep,
    limit: Annotated[int, Query(ge=1, le=200, description="Maximum number of items")] = 50,
) -> list[ActivityItem]:
    return [ActivityItem(**item) for item in await list_recent_activity(db, limit)]
