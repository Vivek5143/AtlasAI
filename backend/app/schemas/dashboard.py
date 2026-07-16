"""Pydantic schemas for dashboard data."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class _SchemaModel(BaseModel):
	"""Shared Pydantic configuration for schema models."""

	model_config = ConfigDict(from_attributes=True)


class DashboardBase(_SchemaModel):
	"""Base schema for dashboard metrics."""

	total_companies: int = 0
	total_sectors: int = 0
	total_problems: int = 0
	total_news_articles: int = 0
	companies_with_sectors: int = 0
	companies_with_news: int = 0
	sectors_with_companies: int = 0
	problems_with_category: int = 0
	problems_with_severity: int = 0


class DashboardCreate(DashboardBase):
	"""Schema used to create dashboard metrics payloads."""


class DashboardUpdate(_SchemaModel):
	"""Schema used to update dashboard metrics payloads."""

	total_companies: Optional[int] = None
	total_sectors: Optional[int] = None
	total_problems: Optional[int] = None
	total_news_articles: Optional[int] = None
	companies_with_sectors: Optional[int] = None
	companies_with_news: Optional[int] = None
	sectors_with_companies: Optional[int] = None
	problems_with_category: Optional[int] = None
	problems_with_severity: Optional[int] = None


class DashboardResponse(DashboardBase):
	"""Schema returned for dashboard metrics."""

	generated_at: datetime


class DashboardListResponse(_SchemaModel):
	"""Schema for a paginated or bulk dashboard response."""

	items: list[DashboardResponse] = Field(default_factory=list)
	total: int = 0
