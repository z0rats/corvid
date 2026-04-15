"""Newsfeed article analysis routes - LLM-based article analysis"""

import logging
from typing import Annotated

from fastapi import APIRouter, Body, HTTPException, Path, status

from app.core.dependencies import SessionDep
from app.features.newsfeed.crud.news_articles_crud import get_news_article_by_id
from app.features.newsfeed.schemas.newsfeed_schemas import (
    AnalysisResultResponse,
    ArticleAnalysisRequest,
)
from app.features.newsfeed.service.article_analysis_service import analyze_article_with_llm
from app.utils.llm_service import get_default_model_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/newsfeed", tags=["Newsfeed"])

ArticleId = Annotated[int, Path(ge=1, description="Article ID")]


@router.post(
    "/analyze/{article_id}",
    response_model=AnalysisResultResponse,
    response_model_exclude_none=True,
    summary="Analyze article",
    description=(
        "Perform LLM-based security analysis on a news article. "
        "When CTI settings are enabled, the analysis is tailored to the configured threat intelligence profile."
    ),
    responses={404: {"description": "Article not found"}},
)
async def analyze_news_article(
    article_id: ArticleId,
    db: SessionDep,
    params: ArticleAnalysisRequest = Body(default_factory=ArticleAnalysisRequest),
) -> AnalysisResultResponse:
    """Analyze a cybersecurity news article with an LLM"""

    article = await get_news_article_by_id(db=db, article_id=article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

    model_id = params.model_id or await get_default_model_id(db, "newsfeed_analysis")

    return await analyze_article_with_llm(
        db=db,
        article_id=article_id,
        model_id=model_id,
        temperature=params.temperature,
        max_tokens=params.max_tokens,
        use_cti_settings=params.use_cti_settings,
        force=params.force,
    )
