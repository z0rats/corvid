import logging

from fastapi import APIRouter, Request, status

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import ReadSessionDep
from app.core.settings.api_keys.schemas.quota_schemas import QuotaStatus
from app.core.settings.api_keys.service.quota_service import get_quota_status

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/api/services/quota",
    response_model=list[QuotaStatus],
    status_code=status.HTTP_200_OK,
    tags=["Service Configuration"],
    summary="Check remaining API quota for configured providers",
    description="Live quota/usage check against VirusTotal, Shodan, and Hunter.io using their configured API keys. "
                 "Other providers don't expose a comparable quota endpoint and are omitted.",
)
@limiter.limit("10/minute")
async def get_quota_status_endpoint(request: Request, db: ReadSessionDep) -> list[QuotaStatus]:
    return await get_quota_status(db)
