"""Newsfeed analytics routes - IOC stats, CVE stats, word frequency"""

import logging

from fastapi import APIRouter, Query

from app.core.dependencies import ReadSessionDep
from app.features.newsfeed.crud.analytics_crud import (
    get_top_iocs,
    get_top_cves,
    get_ioc_type_distribution,
    get_title_word_frequency,
)
from app.features.newsfeed.schemas.newsfeed_schemas import (
    CveEntry,
    IocDistributionEntry,
    IocEntry,
    IocType,
    WordFrequencyEntry,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/newsfeed", tags=["Newsfeed"])


@router.get(
    "/iocs/top",
    response_model=list[IocEntry],
    summary="Top IOCs",
    description="Get the most frequent IOCs of a specific type within a given time range",
)
async def get_top_iocs_route(
    db: ReadSessionDep,
    ioc_type: IocType = Query(..., description="IOC type (e.g., ips, md5_hashes, domains)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results to return"),
    time_range: str = Query("7d", description="Time range (e.g., 8h, 24h, 2d, 7d, 14d, 30d)"),
) -> list[IocEntry]:
    """Get top N most frequent IOCs of a specific type within a given time range"""
    return await get_top_iocs(db, ioc_type, limit, time_range)


@router.get(
    "/cves/top",
    response_model=list[CveEntry],
    summary="Top CVEs",
    description="Get the most frequently mentioned CVEs within a given time range",
)
async def get_top_cves_route(
    db: ReadSessionDep,
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results to return"),
    time_range: str = Query("7d", description="Time range (e.g., 8h, 24h, 2d, 7d, 14d, 30d)"),
) -> list[CveEntry]:
    """Get top N most frequent CVEs within a given time range"""
    return await get_top_cves(db, limit, time_range)


@router.get(
    "/iocs/distribution",
    response_model=list[IocDistributionEntry],
    summary="IOC type distribution",
    description="Get the distribution of IOC types across articles within a given time range",
)
async def get_ioc_distribution_route(
    db: ReadSessionDep,
    time_range: str = Query("7d", description="Time range (e.g., 8h, 24h, 2d, 7d, 14d, 30d)"),
) -> list[IocDistributionEntry]:
    """Get the distribution of IOC types within a given time range, sorted by count descending"""
    return await get_ioc_type_distribution(db, time_range)


@router.get(
    "/words/top",
    response_model=list[WordFrequencyEntry],
    summary="Top words",
    description="Get the most frequent words in article titles within a given time range",
)
async def get_top_words_route(
    db: ReadSessionDep,
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results to return"),
    time_range: str = Query("7d", description="Time range (e.g., 8h, 24h, 2d, 7d, 14d, 30d)"),
) -> list[WordFrequencyEntry]:
    """Get top N most frequent words in article titles within a given time range"""
    words_data = await get_title_word_frequency(db, limit, time_range)
    return words_data if words_data else []
