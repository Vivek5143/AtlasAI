"""Company repository for database operations."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.company import Company
from app.models.company_sector import CompanySector
from app.models.problem_company_mapping import ProblemCompanyMapping
from app.models.sector import Sector


class CompanyRepository:
    """Repository for company database operations only."""

    def __init__(self, session: Session) -> None:
        """Initialize the repository.

        Args:
            session: Active SQLAlchemy session.
        """

        self.session = session

    def _hydrate_company(self, company: Company) -> Company:
        """Return a company hydrated through eager-loaded relationships."""

        return company

    def _company_query(self):
        """Build a company query with eager-loaded relationships."""

        return select(Company).options(
            selectinload(Company.company_sectors).selectinload(CompanySector.sector),
            selectinload(Company.problem_mappings).selectinload(ProblemCompanyMapping.problem),
            selectinload(Company.news_articles),
        )

    def get_all(self) -> list[Company]:
        """Return all companies ordered by vendor name."""

        statement = self._company_query().order_by(Company.vendor_name.asc())
        return [self._hydrate_company(company) for company in self.session.execute(statement).scalars().all()]

    def get_by_id(self, company_id: UUID) -> Company | None:
        """Return a company by primary key."""

        statement = self._company_query().where(Company.id == company_id)
        company = self.session.execute(statement).scalars().first()
        return self._hydrate_company(company) if company is not None else None

    def get_by_vendor_name(self, name: str) -> Company | None:
        """Return a company by vendor name."""

        statement = self._company_query().where(func.lower(Company.vendor_name) == name.strip().lower())
        company = self.session.execute(statement).scalars().first()
        return self._hydrate_company(company) if company is not None else None

    def search(self, keyword: str) -> list[Company]:
        """Search companies by common text fields."""

        pattern = f"%{keyword.strip()}%"
        statement = (
            self._company_query()
            .where(
                or_(
                    Company.vendor_name.ilike(pattern),
                    Company.country.ilike(pattern),
                    Company.company_type.ilike(pattern),
                    Company.ai_category.ilike(pattern),
                    Company.funding.ilike(pattern),
                    Company.estimated_revenue.ilike(pattern),
                    Company.maturity.ilike(pattern),
                    Company.deployment_evidence.ilike(pattern),
                )
            )
            .order_by(Company.vendor_name.asc())
        )
        return [self._hydrate_company(company) for company in self.session.execute(statement).scalars().all()]

    def get_by_sector(self, sector_name: str) -> list[Company]:
        """Return companies associated with a sector name."""

        statement = (
            self._company_query()
            .join(Company.company_sectors)
            .join(CompanySector.sector)
            .where(func.lower(Sector.name) == sector_name.strip().lower())
            .order_by(Company.vendor_name.asc())
            .distinct()
        )
        return [self._hydrate_company(company) for company in self.session.execute(statement).scalars().all()]

    def create(self, company: Company) -> Company:
        """Persist a new company."""

        self.session.add(company)
        self.session.commit()
        self.session.refresh(company)
        return self._hydrate_company(company)

    def update(self, company: Company) -> Company:
        """Persist company changes."""

        merged_company = self.session.merge(company)
        self.session.commit()
        self.session.refresh(merged_company)
        return self._hydrate_company(merged_company)

    def delete(self, company_id: UUID) -> bool:
        """Delete a company by identifier."""

        statement = delete(Company).where(Company.id == company_id)
        result = self.session.execute(statement)
        self.session.commit()
        return (result.rowcount or 0) > 0

    def count(self) -> int:
        """Return the total number of companies."""

        statement = select(func.count()).select_from(Company)
        return int(self.session.execute(statement).scalar_one())
