"""News endpoints.

Provides read-only APIs for accessing persisted news articles.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends


from app.api.v1.dependencies import get_news_service
from app.schemas.news import NewsListResponse

router = APIRouter(prefix="/news", tags=["News"])


@router.get("", response_model=NewsListResponse)
async def list_news(news_service=Depends(get_news_service)) -> NewsListResponse:
    """List the most recent news articles."""

    # Use a deterministic default to keep this endpoint production-friendly.
    articles = news_service.get_recent_news(limit=50)
    return NewsListResponse(items=articles, total=len(articles))


@router.get("/company/{company_id}", response_model=NewsListResponse)
async def list_company_news(
    company_id: UUID,
    news_service=Depends(get_news_service),
) -> NewsListResponse:
    """List the most recent news articles for a given company id."""

    articles = news_service.get_company_news(company_id=company_id, limit=50)
    return NewsListResponse(items=articles, total=len(articles))

