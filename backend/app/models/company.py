"""SQLAlchemy model for storing company records."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.database.base import Base
from app.utils.datetime import utc_now

if TYPE_CHECKING:
    from app.models.news_article import NewsArticle
    from app.models.problem import Problem
    from app.models.sector import Sector


class Company(Base):
    """Represents a company in the AI Business Intelligence Platform."""

    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    vendor_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    country: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    website: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        index=True,
    )

    company_type: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    ai_category: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    funding: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    estimated_revenue: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    maturity: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    deployment_evidence: Mapped[str | None] = mapped_column(
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

    company_sectors: Mapped[list["CompanySector"]] = relationship(
        "CompanySector",
        back_populates="company",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    problem_mappings: Mapped[list["ProblemCompanyMapping"]] = relationship(
        "ProblemCompanyMapping",
        back_populates="company",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    news_articles: Mapped[list["NewsArticle"]] = relationship(
        "NewsArticle",
        back_populates="company",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def sectors(self) -> list["Sector"]:
        """Return normalized sectors linked to the company."""

        return sorted(
            [company_sector.sector for company_sector in self.company_sectors if company_sector.sector],
            key=lambda sector: sector.name.lower(),
        )

    @property
    def problems(self) -> list["Problem"]:
        """Return related problems linked through mapping rows."""

        return sorted(
            [mapping.problem for mapping in self.problem_mappings if mapping.problem],
            key=lambda problem: problem.name.lower(),
        )

    @property
    def news(self) -> list["NewsArticle"]:
        """Return related news articles ordered newest first."""

        return sorted(
            self.news_articles,
            key=lambda article: article.published_at,
            reverse=True,
        )


from app.models.company_sector import CompanySector  # noqa: E402,F401
from app.models.news_article import NewsArticle  # noqa: E402,F401
from app.models.problem import Problem  # noqa: E402,F401
from app.models.problem_company_mapping import ProblemCompanyMapping  # noqa: E402,F401
from app.models.sector import Sector  # noqa: E402,F401
