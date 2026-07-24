"""SQLAlchemy model for untrusted company discovery candidates."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Float, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON, Uuid

from app.database.base import Base
from app.utils.datetime import utc_now


class CompanyDiscoveryStatus(str, Enum):
    """Review status for a discovered company candidate."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class CompanyDiscoveryCandidate(Base):
    """Represents an externally evidenced company candidate awaiting review."""

    __tablename__ = "company_discovery_candidates"
    __table_args__ = (
        Index(
            "ix_company_discovery_candidates_status_score_discovered",
            "status",
            "confidence_score",
            "discovered_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    company_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    website_domain: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="tavily", index=True)
    provider_company_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    provider_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    evidence_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    evidence_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    evidence_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_domain: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    confidence_reasons: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=CompanyDiscoveryStatus.PENDING.value,
        index=True,
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_company_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True,
        index=True,
    )
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
