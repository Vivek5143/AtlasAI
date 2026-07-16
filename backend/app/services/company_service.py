"""Company service layer."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from app.models.company import Company
from app.repositories.company_repository import CompanyRepository
from sqlalchemy.orm import Session


class CompanyService:
    """Business logic for company operations."""

    def __init__(self, repository: CompanyRepository | Session, logger: logging.Logger | None = None) -> None:
        """Initialize the service.

        Args:
            repository: Company repository instance or SQLAlchemy session.
            logger: Optional logger instance.
        """

        self.repository = repository if isinstance(repository, CompanyRepository) else CompanyRepository(repository)
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def get_all_companies(self) -> list[Company]:
        """Return all companies."""

        self.logger.debug("Fetching all companies.")
        return self.repository.get_all()

    def get_company(self, company_id: UUID) -> Company | None:
        """Return a company by identifier."""

        self.logger.debug("Fetching company %s.", company_id)
        return self.repository.get_by_id(company_id)

    def search_companies(self, keyword: str) -> list[Company]:
        """Search companies by keyword."""

        if not keyword or not keyword.strip():
            return []

        self.logger.debug("Searching companies with keyword '%s'.", keyword)
        return self.repository.search(keyword)

    def get_companies_by_sector(self, sector: str) -> list[Company]:
        """Return companies associated with a sector name."""

        if not sector or not sector.strip():
            return []

        self.logger.debug("Fetching companies for sector '%s'.", sector)
        return self.repository.get_by_sector(sector)

    def _build_company(self, company_data: Company | dict[str, Any]) -> Company:
        """Build a Company ORM object from input data."""

        if isinstance(company_data, Company):
            return company_data

        if not company_data.get("vendor_name"):
            raise ValueError("vendor_name is required to create a company.")

        return Company(**company_data)

    def create_company(self, company_data: Company | dict[str, Any]) -> Company:
        """Create a company."""

        company = self._build_company(company_data)
        self.logger.info("Creating company '%s'.", company.vendor_name)
        return self.repository.create(company)

    def update_company(self, company_id: UUID, updates: dict[str, Any]) -> Company:
        """Update a company."""

        company = self.repository.get_by_id(company_id)
        if company is None:
            raise LookupError(f"Company '{company_id}' not found.")

        for field_name, field_value in updates.items():
            if hasattr(company, field_name):
                setattr(company, field_name, field_value)

        self.logger.info("Updating company '%s'.", company_id)
        return self.repository.update(company)

    def delete_company(self, company_id: UUID) -> bool:
        """Delete a company by identifier."""

        self.logger.info("Deleting company '%s'.", company_id)
        deleted = self.repository.delete(company_id)
        if not deleted:
            raise LookupError(f"Company '{company_id}' not found.")
        return deleted

    def company_statistics(self) -> dict[str, int]:
        """Return basic company statistics."""

        companies = self.repository.get_all()
        companies_with_sectors = sum(1 for company in companies if company.company_sectors)
        companies_with_news = sum(1 for company in companies if company.news_articles)
        return {
            "total_companies": self.repository.count(),
            "companies_with_sectors": companies_with_sectors,
            "companies_with_news": companies_with_news,
        }
