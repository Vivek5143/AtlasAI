"""Sector repository for database operations."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.company import Company
from app.models.company_sector import CompanySector
from app.models.problem_company_mapping import ProblemCompanyMapping
from app.models.sector import Sector


class SectorRepository:
    """Repository for sector database operations only."""

    def __init__(self, session: Session) -> None:
        """Initialize the repository.

        Args:
            session: Active SQLAlchemy session.
        """

        self.session = session

    def _hydrate_company(self, company: Company) -> Company:
        """Return a company hydrated through eager-loaded relationships."""

        return company

    def _sector_query(self):
        """Build a sector query with eager-loaded relationships."""

        return select(Sector).options(
            selectinload(Sector.company_sectors).selectinload(CompanySector.company),
        )

    def get_all(self) -> list[Sector]:
        """Return all sectors ordered by name."""

        statement = self._sector_query().order_by(Sector.name.asc())
        return list(self.session.execute(statement).scalars().all())

    def get_by_id(self, sector_id: UUID) -> Sector | None:
        """Return a sector by primary key."""

        statement = self._sector_query().where(Sector.id == sector_id)
        return self.session.execute(statement).scalars().first()

    def get_by_name(self, name: str) -> Sector | None:
        """Return a sector by name."""

        statement = self._sector_query().where(func.lower(Sector.name) == name.strip().lower())
        return self.session.execute(statement).scalars().first()

    def get_companies(self, sector_id: UUID) -> list[Company]:
        """Return companies associated with a sector identifier."""

        statement = (
            select(Company)
            .options(
                selectinload(Company.company_sectors).selectinload(CompanySector.sector),
                selectinload(Company.problem_mappings).selectinload(ProblemCompanyMapping.problem),
                selectinload(Company.news_articles),
            )
            .join(Company.company_sectors)
            .where(CompanySector.sector_id == sector_id)
            .order_by(Company.vendor_name.asc())
            .distinct()
        )
        return [self._hydrate_company(company) for company in self.session.execute(statement).scalars().all()]

    def create(self, sector: Sector) -> Sector:
        """Persist a new sector."""

        self.session.add(sector)
        self.session.commit()
        self.session.refresh(sector)
        return sector

    def update(self, sector: Sector) -> Sector:
        """Persist sector changes."""

        merged_sector = self.session.merge(sector)
        self.session.commit()
        self.session.refresh(merged_sector)
        return merged_sector

    def delete(self, sector_id: UUID) -> bool:
        """Delete a sector by identifier."""

        statement = delete(Sector).where(Sector.id == sector_id)
        result = self.session.execute(statement)
        self.session.commit()
        return (result.rowcount or 0) > 0

    def count(self) -> int:
        """Return the total number of sectors."""

        statement = select(func.count()).select_from(Sector)
        return int(self.session.execute(statement).scalar_one())
