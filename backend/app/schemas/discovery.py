"""Pydantic schemas for company discovery review workflows."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.company import CompanyResponse


class _SchemaModel(BaseModel):
    """Shared Pydantic configuration for discovery schemas."""

    model_config = ConfigDict(from_attributes=True)


class CompanyDiscoveryRequest(_SchemaModel):
    """Request payload for external company discovery."""

    query: Optional[str] = None
    sector: Optional[str] = None
    country: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=50)


class CompanyDiscoveryCandidateResponse(_SchemaModel):
    """Response schema for discovery candidates."""

    id: UUID
    company_name: str
    normalized_name: str
    website: Optional[str] = None
    website_domain: Optional[str] = None
    country: Optional[str] = None
    description: Optional[str] = None
    ai_category: Optional[str] = None
    provider: str = "tavily"
    provider_company_id: Optional[str] = None
    provider_metadata: Optional[dict] = None
    evidence_url: str
    evidence_title: Optional[str] = None
    evidence_text: Optional[str] = None
    source_domain: Optional[str] = None
    confidence_score: float
    confidence_reasons: list[str] = Field(default_factory=list)
    status: str
    rejection_reason: Optional[str] = None
    approved_company_id: Optional[UUID] = None
    discovered_at: datetime
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class CompanyDiscoverySkippedCandidate(_SchemaModel):
    """A provider result skipped before pending review creation."""

    company_name: Optional[str] = None
    evidence_url: Optional[str] = None
    reason: str


class CompanyDiscoveryProviderExtractionDetail(_SchemaModel):
    """Safe provider extraction diagnostic for a skipped article."""

    title: Optional[str] = None
    source_domain: Optional[str] = None
    extraction_skip_reason: str


class CompanyDiscoverySummary(_SchemaModel):
    """Summary returned after a discovery run."""

    candidates_found: int = 0
    candidates_created: int = 0
    candidates_skipped: int = 0
    articles_fetched: int = 0
    provider_candidates_extracted: int = 0
    provider_extraction_skipped: int = 0
    items: list[CompanyDiscoveryCandidateResponse] = Field(default_factory=list)
    skipped: list[CompanyDiscoverySkippedCandidate] = Field(default_factory=list)
    provider_extraction_details: list[CompanyDiscoveryProviderExtractionDetail] = Field(default_factory=list)


class CompanyDiscoveryListResponse(_SchemaModel):
    """Bulk response for pending discovery candidates."""

    items: list[CompanyDiscoveryCandidateResponse] = Field(default_factory=list)
    total: int = 0


class CompanyDiscoveryApprovalResponse(_SchemaModel):
    """Response returned after approving a candidate."""

    company: CompanyResponse
    indexing_status: str
    indexed_chunks: int = 0


class CompanyDiscoveryRejectionRequest(_SchemaModel):
    """Payload for rejecting a discovery candidate."""

    rejection_reason: Optional[str] = None
