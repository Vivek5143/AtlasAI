"""Pydantic schemas for the AtlasAI ask endpoint."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class _SchemaModel(BaseModel):
    """Shared Pydantic configuration for schema models."""

    model_config = ConfigDict(from_attributes=True)


class AskAIRequest(_SchemaModel):
    """Request payload for the AtlasAI RAG endpoint."""

    question: str = Field(min_length=1)


class AskAIMetadata(_SchemaModel):
    """Serializable metadata for a retrieved RAG source chunk."""

    id: Optional[str] = None
    entity_type: Optional[str] = None
    title: Optional[str] = None
    created_at: Optional[str] = None
    company_id: Optional[str] = None
    problem_id: Optional[str] = None
    news_id: Optional[str] = None
    sector_id: Optional[str] = None
    source: Optional[str] = None
    chunk_index: Optional[int] = None
    score: Optional[float] = None


class AskAIResponse(_SchemaModel):
    """Response payload for the AtlasAI RAG endpoint."""

    answer: str
    sources: list[str] = Field(default_factory=list)
    metadata: list[AskAIMetadata] = Field(default_factory=list)
