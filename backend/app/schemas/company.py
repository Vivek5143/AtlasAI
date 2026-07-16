"""Pydantic schemas for company data."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class _SchemaModel(BaseModel):
	"""Shared Pydantic configuration for schema models."""

	model_config = ConfigDict(from_attributes=True)


class CompanyBase(_SchemaModel):
	"""Base schema for company data.

	Attributes:
		vendor_name: Public company name.
		country: Country where the company is based.
		website: Company website URL.
		company_type: Company type or classification.
		ai_category: AI category associated with the company.
		funding: Funding stage or amount.
		estimated_revenue: Estimated revenue band.
		maturity: Company maturity stage.
		deployment_evidence: Supporting deployment evidence.
	"""

	vendor_name: str
	country: Optional[str] = None
	website: Optional[str] = None
	company_type: Optional[str] = None
	ai_category: Optional[str] = None
	funding: Optional[str] = None
	estimated_revenue: Optional[str] = None
	maturity: Optional[str] = None
	deployment_evidence: Optional[str] = None


class CompanyCreate(CompanyBase):
	"""Schema used to create a company."""


class CompanyUpdate(_SchemaModel):
	"""Schema used to update a company."""

	vendor_name: Optional[str] = None
	country: Optional[str] = None
	website: Optional[str] = None
	company_type: Optional[str] = None
	ai_category: Optional[str] = None
	funding: Optional[str] = None
	estimated_revenue: Optional[str] = None
	maturity: Optional[str] = None
	deployment_evidence: Optional[str] = None


class CompanyResponse(CompanyBase):
	"""Schema returned for company responses."""

	id: UUID
	created_at: datetime
	updated_at: datetime


class CompanyListResponse(_SchemaModel):
	"""Schema for a paginated or bulk company response."""

	items: list[CompanyResponse] = Field(default_factory=list)
	total: int = 0
