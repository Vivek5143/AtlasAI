"""Business logic for synchronizing news articles."""

from __future__ import annotations

import logging
import re
import string
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.clients.news_api_client import NewsApiClient
from app.models.company import Company
from app.models.news_article import NewsArticle
from app.repositories.news_repository import NewsRepository


class NewsService:
    """Service responsible for fetching and storing news articles."""

    def __init__(
        self,
        session: Session,
        client: NewsApiClient | None = None,
        repository: NewsRepository | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.session = session
        self.client = client or NewsApiClient()
        self.repository = repository or NewsRepository(session)
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    # ---------------------------------------------------------
    # Database Helpers
    # ---------------------------------------------------------

    def _load_companies(self) -> list[Company]:
        """Load all companies from the database."""

        statement = select(Company).order_by(Company.vendor_name.asc())
        return list(self.session.execute(statement).scalars().all())

    def _find_company_by_name(self, company_name: str) -> Company | None:
        """Find a company using partial case-insensitive matching."""

        if not company_name:
            return None

        statement = (
            select(Company)
            .where(Company.vendor_name.ilike(f"%{company_name.strip()}%"))
            .limit(1)
        )

        return self.session.execute(statement).scalars().first()

    # ---------------------------------------------------------
    # Normalization Helpers
    # ---------------------------------------------------------

    @staticmethod
    def _normalize_company_name(name: str) -> str:
        """Normalize a company name for comparison."""

        if not name:
            return ""

        value = name.lower()

        suffixes = [
            " ag",
            " se",
            " gmbh",
            " ltd",
            " ltd.",
            " llc",
            " inc",
            " inc.",
            " corporation",
            " corp",
            " corp.",
            " plc",
            " co.",
            " company",
        ]

        for suffix in suffixes:
            if value.endswith(suffix):
                value = value[: -len(suffix)]

        value = value.translate(
            str.maketrans("", "", string.punctuation)
        )

        value = re.sub(r"\s+", " ", value)

        return value.strip()

    def _article_text(self, article: dict[str, Any]) -> str:
        """Return searchable article text."""

        return " ".join(
            [
                str(article.get("title") or ""),
                str(article.get("description") or ""),
                str(article.get("content") or ""),
            ]
        ).lower()

    def _match_company_from_text(
        self,
        article: dict[str, Any],
        companies: list[Company],
    ) -> Company | None:
        """Match an article to the most likely company."""

        searchable_text = self._normalize_company_name(
            self._article_text(article)
        )

        best_match: Company | None = None
        longest = 0

        for company in companies:

            vendor = company.vendor_name

            normalized = self._normalize_company_name(vendor)

            if normalized and normalized in searchable_text:

                if len(normalized) > longest:
                    longest = len(normalized)
                    best_match = company
                    continue

            first_word = normalized.split(" ")[0]

            if len(first_word) >= 3 and first_word in searchable_text:

                if len(first_word) > longest:
                    longest = len(first_word)
                    best_match = company

        return best_match

    # ---------------------------------------------------------
    # Date Helpers
    # ---------------------------------------------------------

    @staticmethod
    def _normalize_published_at(value: Any) -> datetime:
        """Normalize published timestamps."""

        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value

        if isinstance(value, str) and value:

            try:
                return datetime.fromisoformat(
                    value.replace("Z", "+00:00")
                )
            except Exception:
                pass

        return datetime.now(timezone.utc)

    # ---------------------------------------------------------
    # ORM Builder
    # ---------------------------------------------------------

    def _build_news_article(
        self,
        article: dict[str, Any],
        company: Company,
    ) -> NewsArticle:
        """Create a NewsArticle ORM object."""

        return NewsArticle(
            company_id=company.id,
            title=str(article.get("title") or "").strip(),
            url=str(article.get("url") or "").strip(),
            published_at=self._normalize_published_at(
                article.get("published_at")
            ),
        )
    # ---------------------------------------------------------
    # Internal Sync Helpers
    # ---------------------------------------------------------

    def _prepare_articles(
        self,
        articles: list[dict[str, Any]],
        company_resolver,
    ) -> list[NewsArticle]:
        """
        Convert normalized NewsAPI responses into ORM objects.

        Removes:
        - duplicate URLs already seen in this batch
        - duplicate URLs already stored in the database
        - articles without titles
        - articles without URLs
        - articles that cannot be matched to a company
        """

        prepared_articles: list[NewsArticle] = []
        seen_urls: set[str] = set()

        inserted = 0
        duplicates = 0
        skipped_company = 0
        skipped_invalid = 0

        for article in articles:

            title = str(article.get("title") or "").strip()
            url = str(article.get("url") or "").strip()

            if not title or not url:
                skipped_invalid += 1
                continue

            if url in seen_urls:
                duplicates += 1
                continue

            if self.repository.article_exists(url):
                duplicates += 1
                continue

            company = company_resolver(article)

            if company is None:
                skipped_company += 1
                continue

            news_article = self._build_news_article(
                article=article,
                company=company,
            )

            prepared_articles.append(news_article)

            seen_urls.add(url)
            inserted += 1

            self.logger.debug(
                "Matched '%s' -> %s",
                title,
                company.vendor_name,
            )

        self.logger.info(
            (
                "Prepared News Articles | "
                "Inserted=%s "
                "Duplicates=%s "
                "NoCompany=%s "
                "Invalid=%s"
            ),
            inserted,
            duplicates,
            skipped_company,
            skipped_invalid,
        )

        return prepared_articles

    def _sync_articles(
        self,
        articles: list[dict[str, Any]],
        company_resolver,
    ) -> list[NewsArticle]:
        """
        Synchronize articles into PostgreSQL.

        Workflow:

        NewsAPI
              ↓
        Normalize
              ↓
        Remove duplicates
              ↓
        Match company
              ↓
        Save
        """

        self.logger.info(
            "Fetched %s article(s) from NewsAPI.",
            len(articles),
        )

        prepared_articles = self._prepare_articles(
            articles=articles,
            company_resolver=company_resolver,
        )

        if not prepared_articles:
            self.logger.info(
                "No new articles available for insertion."
            )
            return []

        try:

            saved_articles = self.repository.save_articles(
                prepared_articles
            )

            self.logger.info(
                "Successfully inserted %s article(s).",
                len(saved_articles),
            )

            return saved_articles

        except Exception as exc:

            self.logger.exception(
                "Failed while saving articles: %s",
                exc,
            )

            self.session.rollback()

            return []
    # ---------------------------------------------------------
    # Public Service Methods
    # ---------------------------------------------------------

    def sync_company_news(self, company_name: str) -> list[NewsArticle]:
        """
        Fetch and store news for a single company.

        Args:
            company_name: Company name supplied by the caller.

        Returns:
            Persisted NewsArticle objects.
        """

        company = self._find_company_by_name(company_name)

        if company is None:
            self.logger.warning(
                "Company '%s' was not found in the database.",
                company_name,
            )
            return []

        self.logger.info(
            "Fetching news for company '%s'.",
            company.vendor_name,
        )

        try:
            articles = self.client.fetch_company_news(
                company.vendor_name
            )

            self.logger.info(
                "Received %s article(s) from NewsAPI.",
                len(articles),
            )

            return self._sync_articles(
                articles=articles,
                company_resolver=lambda _: company,
            )

        except Exception as exc:
            self.logger.exception(
                "Company news synchronization failed: %s",
                exc,
            )
            return []

    def sync_sector_news(self, sector_name: str) -> list[NewsArticle]:
        """
        Fetch and store news related to a sector.

        Args:
            sector_name: Sector search term.

        Returns:
            Persisted NewsArticle objects.
        """

        companies = self._load_companies()

        self.logger.info(
            "Fetching sector news for '%s'.",
            sector_name,
        )

        try:

            articles = self.client.fetch_sector_news(
                sector_name
            )

            self.logger.info(
                "Received %s article(s).",
                len(articles),
            )

            return self._sync_articles(
                articles=articles,
                company_resolver=lambda article:
                    self._match_company_from_text(
                        article,
                        companies,
                    ),
            )

        except Exception as exc:

            self.logger.exception(
                "Sector synchronization failed: %s",
                exc,
            )

            return []

    def sync_latest_news(self) -> list[NewsArticle]:
        """
        Fetch the latest news and associate articles
        with companies found in the database.

        Returns:
            Persisted NewsArticle objects.
        """

        companies = self._load_companies()

        self.logger.info(
            "Fetching latest news."
        )

        try:

            articles = self.client.fetch_latest()

            self.logger.info(
                "Received %s latest article(s).",
                len(articles),
            )

            return self._sync_articles(
                articles=articles,
                company_resolver=lambda article:
                    self._match_company_from_text(
                        article,
                        companies,
                    ),
            )

        except Exception as exc:

            self.logger.exception(
                "Latest news synchronization failed: %s",
                exc,
            )

            return []

    def search_news(self, query: str) -> list[NewsArticle]:
        """
        Search NewsAPI using an arbitrary query.

        Args:
            query: Search keyword.

        Returns:
            Persisted NewsArticle objects.
        """

        companies = self._load_companies()

        self.logger.info(
            "Searching NewsAPI for '%s'.",
            query,
        )

        try:

            articles = self.client.fetch_everything(query)

            self.logger.info(
                "Received %s article(s).",
                len(articles),
            )

            return self._sync_articles(
                articles=articles,
                company_resolver=lambda article:
                    self._match_company_from_text(
                        article,
                        companies,
                    ),
            )

        except Exception as exc:

            self.logger.exception(
                "News search failed: %s",
                exc,
            )

            return []            