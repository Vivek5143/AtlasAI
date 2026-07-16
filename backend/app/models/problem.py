"""SQLAlchemy model for business problems identified in the dataset."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.database.base import Base
from app.utils.datetime import utc_now


class Problem(Base):
    """Represents a business problem that AI vendors can solve."""

    __tablename__ = "problems"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Original ID from the CSV (P1, P2, ...)
    external_problem_id: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        unique=True,
        index=True,
    )

    # Example: Quality Control
    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # Main problem statement
    name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        unique=True,
        index=True,
    )

    # Example: Operational, Strategic, Compliance
    problem_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # Example: Early Stage, Growth Stage, Enterprise
    vc_stage: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # High / Medium / Low
    severity: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    financial_impact: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    regulatory_trigger: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    ai_solution: Mapped[str | None] = mapped_column(
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

    company_mappings: Mapped[list["ProblemCompanyMapping"]] = relationship(
        "ProblemCompanyMapping",
        back_populates="problem",
        cascade="all, delete-orphan",
        lazy="selectin",
    )