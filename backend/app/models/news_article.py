"""SQLAlchemy model for news articles captured in the company dataset."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.database.base import Base
from app.utils.datetime import utc_now


class NewsArticle(Base):
    """Represents a news article associated with a single company."""

    __tablename__ = "news_articles"
    __table_args__ = (
        Index(
            "ix_news_articles_company_id_published_at",
            "company_id",
            "published_at",
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

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
    )

    url: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
        unique=True,
        index=True,
    )

    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
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

    company: Mapped["Company"] = relationship(
        "Company",
        back_populates="news_articles",
        lazy="selectin",
    )

    @property
    def company_name(self) -> str | None:
        """Return the associated company name when loaded."""

        return self.company.vendor_name if self.company is not None else None
