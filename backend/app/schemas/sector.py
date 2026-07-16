"""Pydantic schemas for sector data."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class _SchemaModel(BaseModel):
	"""Shared Pydantic configuration for schema models."""

	model_config = ConfigDict(from_attributes=True)


class SectorBase(_SchemaModel):
	"""Base schema for sector data.

	Attributes:
		name: Normalized sector name.
	"""

	name: str


class SectorCreate(SectorBase):
	"""Schema used to create a sector."""


class SectorUpdate(_SchemaModel):
	"""Schema used to update a sector."""

	name: Optional[str] = None


class SectorResponse(SectorBase):
	"""Schema returned for sector responses."""

	id: UUID
	created_at: datetime
	updated_at: datetime


class SectorListResponse(_SchemaModel):
	"""Schema for a paginated or bulk sector response."""

	items: list[SectorResponse] = Field(default_factory=list)
	total: int = 0
