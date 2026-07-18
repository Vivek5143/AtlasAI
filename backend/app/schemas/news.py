"""Pydantic schemas for news article data."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class _SchemaModel(BaseModel):
    """Shared Pydantic configuration for schema models."""

    model_config = ConfigDict(
        from_attributes=True
    )


class NewsBase(_SchemaModel):
    """Base schema for news article data."""

    company_id: UUID
    title: str
    url: str
    published_at: datetime


class NewsCreate(NewsBase):
    """Schema used to create a news article."""

    pass


class NewsUpdate(_SchemaModel):
    """Schema used to update a news article."""

    company_id: Optional[UUID] = None
    title: Optional[str] = None
    url: Optional[str] = None
    published_at: Optional[datetime] = None


class NewsResponse(NewsBase):
    """Schema returned for news article responses."""

    id: UUID
    created_at: datetime
    updated_at: datetime
    company_name: Optional[str] = None


class NewsListResponse(_SchemaModel):
    """Schema for a paginated or bulk news response."""

    items: list[NewsResponse] = Field(
        default_factory=list
    )
    total: int = 0


class NewsRefreshSummary(_SchemaModel):
    """Summary payload returned after a refresh sync attempt."""

    companies_checked: int = 0
    companies_total: int = 0
    rotation_offset: int = 0

    articles_fetched: int = 0
    articles_created: int = 0
    articles_updated: int = 0
    articles_skipped: int = 0

    articles_duplicates: int = 0
    articles_rejected_irrelevant: int = 0

    skip_reasons: dict[str, int] = Field(
        default_factory=dict
    )

    rag_news_indexed: int = 0
    rag_indexing_status: str = "not_attempted"


class NewsRefreshResponse(_SchemaModel):
    """Refresh endpoint response wrapper."""

    items: NewsRefreshSummary


class NewsReindexSummary(_SchemaModel):
    """Summary payload returned after manual news reindexing."""

    status: str = "indexed"

    stale_news_vectors_deleted: int = 0

    news_records_found: int = 0
    news_records_indexed: int = 0
    news_chunks_indexed: int = 0