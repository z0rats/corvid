from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, status

from app.core.dependencies import ReadSessionDep, SessionDep
from app.features.newsfeed.schemas.newsfeed_schemas import (
    ArticleIocsResponse,
    BulkArticleRequest,
    NewsArticleSchema,
    UpdateArticleRequest,
)
from app.features.newsfeed.service.article_retrieval_service import (
    get_article as get_article_service,
    get_articles_bulk as get_articles_bulk_service,
    update_article_details as update_article_service,
    get_article_iocs as get_article_iocs_service,
)

router = APIRouter(prefix="/api/newsfeed", tags=["Newsfeed"])

ArticleId = Annotated[int, Path(ge=1, description="Article ID")]


@router.get(
    "/article/{article_id}",
    response_model=NewsArticleSchema,
    response_model_exclude_none=True,
    summary="Get article",
    description="Retrieve a single news article by its ID",
    responses={404: {"description": "Article not found"}},
)
async def get_article(article_id: ArticleId, db: ReadSessionDep) -> NewsArticleSchema:
    article = await get_article_service(db, article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    return article


@router.post(
    "/articles/bulk",
    response_model=list[NewsArticleSchema],
    response_model_exclude_none=True,
    summary="Bulk fetch articles",
    description="Retrieve multiple news articles by their IDs in a single request (max 200)",
)
async def get_articles_bulk(request: BulkArticleRequest, db: ReadSessionDep) -> list[NewsArticleSchema]:
    return await get_articles_bulk_service(db, request.article_ids)


@router.patch(
    "/article/{article_id}",
    response_model=NewsArticleSchema,
    response_model_exclude_none=True,
    summary="Update article",
    description="Update article note, TLP classification, or read status",
    responses={404: {"description": "Article not found"}},
)
async def update_article_endpoint(
    article_id: ArticleId,
    update_data: UpdateArticleRequest,
    db: SessionDep,
) -> NewsArticleSchema:
    article = await update_article_service(
        db, article_id, note=update_data.note, tlp=update_data.tlp, read=update_data.read
    )
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    return article


@router.get(
    "/article/{article_id}/iocs",
    response_model=ArticleIocsResponse,
    summary="Get article IOCs",
    description="Get all extracted indicators of compromise for a specific article",
    responses={404: {"description": "Article not found"}},
)
async def get_article_iocs(article_id: ArticleId, db: ReadSessionDep) -> ArticleIocsResponse:
    result = await get_article_iocs_service(db, article_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    return result
