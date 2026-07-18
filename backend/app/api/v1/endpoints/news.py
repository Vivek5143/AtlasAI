"""News endpoints.

Provides read-only APIs for accessing persisted news articles.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.ai import IndexingError

from app.api.v1.dependencies import get_news_service, get_news_sync_service
from app.schemas.news import NewsListResponse, NewsRefreshSummary, NewsReindexSummary
from app.services.news_sync_service import (
    NewsApiAuthenticationError,
    NewsApiConfigurationError,
    NewsApiRateLimitError,
    NewsApiRequestError,
    NewsApiResponseError,
)

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


@router.post("/refresh", response_model=NewsRefreshSummary, status_code=status.HTTP_200_OK)
async def refresh_news(news_sync_service=Depends(get_news_sync_service)) -> NewsRefreshSummary:
    """Trigger company-focused NewsAPI synchronization and return a summary."""

    try:
        summary = news_sync_service.refresh_latest_news()
    except NewsApiConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except NewsApiAuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except NewsApiRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc
    except (NewsApiRequestError, NewsApiResponseError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return NewsRefreshSummary(**summary.to_dict())


@router.post("/reindex", response_model=NewsReindexSummary, status_code=status.HTTP_200_OK)
async def reindex_news(news_sync_service=Depends(get_news_sync_service)) -> NewsReindexSummary:
    """Manually reindex all persisted news articles into ChromaDB."""

    try:
        summary = news_sync_service.reindex_all_persisted_news()
    except IndexingError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return NewsReindexSummary(**summary)
