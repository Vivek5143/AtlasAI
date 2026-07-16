"""SQLAlchemy association model linking companies to sectors."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.database.base import Base


class CompanySector(Base):
    """Represents the many-to-many association between companies and sectors."""

    __tablename__ = "company_sectors"
    __table_args__ = (
        Index("ix_company_sectors_sector_id_company_id", "sector_id", "company_id"),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )

    sector_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("sectors.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )

    company: Mapped["Company"] = relationship(
        "Company",
        back_populates="company_sectors",
        lazy="selectin",
    )

    sector: Mapped["Sector"] = relationship(
        "Sector",
        back_populates="company_sectors",
        lazy="selectin",
    )
