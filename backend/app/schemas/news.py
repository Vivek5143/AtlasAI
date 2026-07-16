"""Pydantic schemas for news article data."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class _SchemaModel(BaseModel):
	"""Shared Pydantic configuration for schema models."""

	model_config = ConfigDict(from_attributes=True)


class NewsBase(_SchemaModel):
	"""Base schema for news article data.

	Attributes:
		company_id: Company identifier associated with the article.
		title: Article title.
		url: Canonical article URL.
		published_at: Publication timestamp.
	"""

	company_id: UUID
	title: str
	url: str
	published_at: datetime


class NewsCreate(NewsBase):
	"""Schema used to create a news article."""


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


class NewsListResponse(_SchemaModel):
	"""Schema for a paginated or bulk news response."""

	items: list[NewsResponse] = Field(default_factory=list)
	total: int = 0
