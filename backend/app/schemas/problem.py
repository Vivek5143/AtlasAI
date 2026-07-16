"""Pydantic schemas for problem data."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class _SchemaModel(BaseModel):
	"""Shared Pydantic configuration for schema models."""

	model_config = ConfigDict(from_attributes=True)


class ProblemBase(_SchemaModel):
	"""Base schema for problem data.

	Attributes:
		external_problem_id: Original problem identifier from the source CSV.
		category: Problem category.
		name: Problem name.
		problem_type: Problem type classification.
		vc_stage: Venture stage associated with the problem.
		severity: Problem severity.
		financial_impact: Financial impact description.
		regulatory_trigger: Regulatory trigger description.
		ai_solution: Suggested AI solution.
	"""

	external_problem_id: Optional[str] = None
	category: Optional[str] = None
	name: str
	problem_type: Optional[str] = None
	vc_stage: Optional[str] = None
	severity: Optional[str] = None
	financial_impact: Optional[str] = None
	regulatory_trigger: Optional[str] = None
	ai_solution: Optional[str] = None


class ProblemCreate(ProblemBase):
	"""Schema used to create a problem."""


class ProblemUpdate(_SchemaModel):
	"""Schema used to update a problem."""

	external_problem_id: Optional[str] = None
	category: Optional[str] = None
	name: Optional[str] = None
	problem_type: Optional[str] = None
	vc_stage: Optional[str] = None
	severity: Optional[str] = None
	financial_impact: Optional[str] = None
	regulatory_trigger: Optional[str] = None
	ai_solution: Optional[str] = None


class ProblemResponse(ProblemBase):
	"""Schema returned for problem responses."""

	id: UUID
	created_at: datetime
	updated_at: datetime


class ProblemListResponse(_SchemaModel):
	"""Schema for a paginated or bulk problem response."""

	items: list[ProblemResponse] = Field(default_factory=list)
	total: int = 0
