"""Sector service layer."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from app.models.sector import Sector
from app.repositories.sector_repository import SectorRepository
from sqlalchemy.orm import Session


class SectorService:
    """Business logic for sector operations."""

    def __init__(self, repository: SectorRepository | Session, logger: logging.Logger | None = None) -> None:
        """Initialize the service.

        Args:
            repository: Sector repository instance or SQLAlchemy session.
            logger: Optional logger instance.
        """

        self.repository = repository if isinstance(repository, SectorRepository) else SectorRepository(repository)
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def get_all_sectors(self) -> list[Sector]:
        """Return all sectors."""

        self.logger.debug("Fetching all sectors.")
        return self.repository.get_all()

    def get_sector(self, sector_id: UUID) -> Sector | None:
        """Return a sector by identifier."""

        self.logger.debug("Fetching sector %s.", sector_id)
        return self.repository.get_by_id(sector_id)

    def get_sector_companies(self, sector_id: UUID) -> list:
        """Return companies associated with a sector."""

        self.logger.debug("Fetching companies for sector %s.", sector_id)
        return self.repository.get_companies(sector_id)

    def _build_sector(self, sector_data: Sector | dict[str, Any]) -> Sector:
        """Build a Sector ORM object from input data."""

        if isinstance(sector_data, Sector):
            return sector_data

        if not sector_data.get("name"):
            raise ValueError("name is required to create a sector.")

        return Sector(**sector_data)

    def create_sector(self, sector_data: Sector | dict[str, Any]) -> Sector:
        """Create a sector."""

        sector = self._build_sector(sector_data)
        self.logger.info("Creating sector '%s'.", sector.name)
        return self.repository.create(sector)

    def update_sector(self, sector_id: UUID, updates: dict[str, Any]) -> Sector:
        """Update a sector."""

        sector = self.repository.get_by_id(sector_id)
        if sector is None:
            raise LookupError(f"Sector '{sector_id}' not found.")

        for field_name, field_value in updates.items():
            if hasattr(sector, field_name):
                setattr(sector, field_name, field_value)

        self.logger.info("Updating sector '%s'.", sector_id)
        return self.repository.update(sector)

    def delete_sector(self, sector_id: UUID) -> bool:
        """Delete a sector by identifier."""

        self.logger.info("Deleting sector '%s'.", sector_id)
        deleted = self.repository.delete(sector_id)
        if not deleted:
            raise LookupError(f"Sector '{sector_id}' not found.")
        return deleted

    def sector_statistics(self) -> dict[str, int]:
        """Return basic sector statistics."""

        sectors = self.repository.get_all()
        sectors_with_companies = sum(1 for sector in sectors if sector.company_sectors)
        return {
            "total_sectors": self.repository.count(),
            "sectors_with_companies": sectors_with_companies,
        }
