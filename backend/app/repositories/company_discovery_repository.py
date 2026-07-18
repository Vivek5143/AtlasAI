"""Repository for company discovery candidate persistence."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.company_discovery_candidate import (
    CompanyDiscoveryCandidate,
    CompanyDiscoveryStatus,
)


class CompanyDiscoveryRepository:
    """Database operations for untrusted discovery candidates."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, candidate: CompanyDiscoveryCandidate) -> CompanyDiscoveryCandidate:
        """Persist a new discovery candidate."""

        self.session.add(candidate)
        self.session.commit()
        self.session.refresh(candidate)
        return candidate

    def update(self, candidate: CompanyDiscoveryCandidate) -> CompanyDiscoveryCandidate:
        """Persist changes to a discovery candidate."""

        merged_candidate = self.session.merge(candidate)
        self.session.commit()
        self.session.refresh(merged_candidate)
        return merged_candidate

    def get_by_id(self, candidate_id: UUID) -> CompanyDiscoveryCandidate | None:
        """Return a candidate by primary key."""

        statement = select(CompanyDiscoveryCandidate).where(
            CompanyDiscoveryCandidate.id == candidate_id
        )
        return self.session.execute(statement).scalars().first()

    def list_pending(self, *, limit: int = 50) -> list[CompanyDiscoveryCandidate]:
        """Return pending candidates ordered for review."""

        statement = (
            select(CompanyDiscoveryCandidate)
            .where(CompanyDiscoveryCandidate.status == CompanyDiscoveryStatus.PENDING.value)
            .order_by(
                CompanyDiscoveryCandidate.confidence_score.desc(),
                CompanyDiscoveryCandidate.discovered_at.desc(),
            )
            .limit(max(1, limit))
        )
        return list(self.session.execute(statement).scalars().all())

    def find_pending_by_normalized_name(
        self,
        normalized_name: str,
    ) -> CompanyDiscoveryCandidate | None:
        """Return a pending candidate matching a normalized company name."""

        statement = select(CompanyDiscoveryCandidate).where(
            CompanyDiscoveryCandidate.status == CompanyDiscoveryStatus.PENDING.value,
            CompanyDiscoveryCandidate.normalized_name == normalized_name,
        )
        return self.session.execute(statement).scalars().first()

    def find_pending_by_website_domain(
        self,
        website_domain: str,
    ) -> CompanyDiscoveryCandidate | None:
        """Return a pending candidate matching a canonical website domain."""

        statement = select(CompanyDiscoveryCandidate).where(
            CompanyDiscoveryCandidate.status == CompanyDiscoveryStatus.PENDING.value,
            CompanyDiscoveryCandidate.website_domain == website_domain,
        )
        return self.session.execute(statement).scalars().first()
