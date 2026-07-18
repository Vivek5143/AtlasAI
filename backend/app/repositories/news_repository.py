"""News article persistence helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Sequence
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, selectinload

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
            .options(selectinload(NewsArticle.company))
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
            .options(selectinload(NewsArticle.company))
            .where(NewsArticle.company_id == company_id)
            .order_by(NewsArticle.published_at.desc())
        )
        return list(self.session.execute(statement).scalars().all())

    def get_all_article_ids(self) -> list[UUID]:
        """Return all persisted news article identifiers."""

        statement = select(NewsArticle.id).order_by(NewsArticle.published_at.desc())
        return list(self.session.execute(statement).scalars().all())

    def get_article_by_url(self, url: str) -> NewsArticle | None:
        """Return an article by canonical URL when present."""

        statement = select(NewsArticle).where(NewsArticle.url == url).limit(1)
        return self.session.execute(statement).scalars().first()

    def get_articles_by_url_prefix(self, url_prefix: str) -> list[NewsArticle]:
        """Return candidate articles whose URLs start with a shared prefix."""

        statement = select(NewsArticle).where(NewsArticle.url.startswith(url_prefix))
        return list(self.session.execute(statement).scalars().all())

    def get_article_by_title_and_published_at(
        self,
        title: str,
        published_at: datetime,
    ) -> NewsArticle | None:
        """Return an article candidate using title + publication time fallback key."""

        statement = (
            select(NewsArticle)
            .where(func.lower(NewsArticle.title) == title.strip().lower())
            .where(NewsArticle.published_at == published_at)
            .limit(1)
        )
        return self.session.execute(statement).scalars().first()

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
