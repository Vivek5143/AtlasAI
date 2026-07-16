"""SQLAlchemy model linking companies to problems in the dataset."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.database.base import Base
from app.utils.datetime import utc_now


class ProblemCompanyMapping(Base):
    """Represents a company-to-problem mapping with implementation metrics."""

    __tablename__ = "problem_company_mappings"
    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "problem_id",
            name="uq_problem_company_mappings_company_id_problem_id",
        ),
        Index(
            "ix_problem_company_mappings_problem_id_company_id",
            "problem_id",
            "company_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    problem_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("problems.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    roi: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    payback: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    implementation_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
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

    company: Mapped["Company"] = relationship(
        "Company",
        back_populates="problem_mappings",
        lazy="selectin",
    )

    problem: Mapped["Problem"] = relationship(
        "Problem",
        back_populates="company_mappings",
        lazy="selectin",
    )
