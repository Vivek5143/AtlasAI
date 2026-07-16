"""SQLAlchemy model for sectors represented in the company dataset."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.database.base import Base
from app.utils.datetime import utc_now

if TYPE_CHECKING:
    from app.models.company_sector import CompanySector


class Sector(Base):
    """Represents a normalized sector value linked to one or more companies."""

    __tablename__ = "sectors"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        unique=True,
        index=True,
    )

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

    company_sectors: Mapped[list["CompanySector"]] = relationship(
        "CompanySector",
        back_populates="sector",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
