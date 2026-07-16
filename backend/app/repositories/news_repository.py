"""News article persistence helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Sequence
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.news_article import NewsArticle


class NewsRepository:
    """Repository for working with news articles."""

    def __init__(self, session: Session) -> None:
        """Initialize the repository.

        Args:
            session: Active SQLAlchemy session.
        """

        self.session = session

    def save_articles(self, articles: Sequence[NewsArticle]) -> list[NewsArticle]:
        """Persist a collection of news articles using one transaction.

        Args:
            articles: Articles to persist.

        Returns:
            list[NewsArticle]: Persisted article objects.
        """

        if not articles:
            return []

        self.session.add_all(list(articles))
        self.session.flush()
        self.session.commit()
        return list(articles)

    def article_exists(self, url: str) -> bool:
        """Check whether an article exists for a URL.

        Args:
            url: Canonical article URL.

        Returns:
            bool: True if an article already exists.
        """

        statement = select(NewsArticle.id).where(NewsArticle.url == url).limit(1)
        return self.session.execute(statement).first() is not None

    def get_recent_articles(self, limit: int) -> list[NewsArticle]:
        """Return the most recent articles ordered by published date.

        Args:
            limit: Maximum number of articles to return.

        Returns:
            list[NewsArticle]: Matching articles.
        """

        statement = (
            select(NewsArticle)
            .order_by(NewsArticle.published_at.desc())
            .limit(limit)
        )
        return list(self.session.execute(statement).scalars().all())

    def get_company_articles(self, company_id: UUID) -> list[NewsArticle]:
        """Return articles for a specific company.

        Args:
            company_id: Company identifier.

        Returns:
            list[NewsArticle]: Matching articles.
        """

        statement = (
            select(NewsArticle)
            .where(NewsArticle.company_id == company_id)
            .order_by(NewsArticle.published_at.desc())
        )
        return list(self.session.execute(statement).scalars().all())

    def delete_old_articles(self, days: int) -> int:
        """Delete articles older than a cutoff.

        Args:
            days: Age threshold in days.

        Returns:
            int: Number of deleted rows.
        """

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        statement = delete(NewsArticle).where(NewsArticle.published_at < cutoff)
        result = self.session.execute(statement)
        self.session.commit()
        return int(result.rowcount or 0)
