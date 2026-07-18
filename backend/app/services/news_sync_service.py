"""Synchronization service for fetching and persisting NewsAPI articles."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import logging
import re
import string
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from uuid import UUID
from app.ai.vector_store import ChromaVectorStoreService

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai import IndexingError, VectorStoreError
from app.ai.ingest import PostgresVectorIngestionService
from app.clients.news_api_client import (
    NewsApiAuthenticationError,
    NewsApiClient,
    NewsApiConfigurationError,
    NewsApiRateLimitError,
    NewsApiRequestError,
    NewsApiResponseError,
)
from app.config.settings import settings
from app.models.company import Company
from app.models.news_article import NewsArticle
from app.repositories.news_repository import NewsRepository


SKIP_REASON_DUPLICATE_URL = "duplicate_url"
SKIP_REASON_DUPLICATE_TITLE = "duplicate_title"
SKIP_REASON_WEAK_COMPANY_MATCH = "weak_company_match"
SKIP_REASON_IRRELEVANT_CONTENT = "irrelevant_content"
SKIP_REASON_INVALID_ARTICLE = "invalid_article"
SKIP_REASON_CROSS_COMPANY_CONFLICT = "cross_company_conflict"
SKIP_REASON_OTHER = "other"

SUPPORTED_SKIP_REASONS = {
    SKIP_REASON_DUPLICATE_URL,
    SKIP_REASON_DUPLICATE_TITLE,
    SKIP_REASON_WEAK_COMPANY_MATCH,
    SKIP_REASON_IRRELEVANT_CONTENT,
    SKIP_REASON_INVALID_ARTICLE,
    SKIP_REASON_CROSS_COMPANY_CONFLICT,
    SKIP_REASON_OTHER,
}

GENERIC_COMPANY_TOKENS = {
    "ai",
    "data",
    "tech",
    "systems",
    "solutions",
    "global",
    "group",
    "labs",
}

TRACKING_QUERY_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_content",
    "utm_term",
}

AUTOMATED_RELEASE_PATTERNS = (
    re.compile(r"\b(changelog|release bot|dependency update|version bump)\b", re.IGNORECASE),
    re.compile(r"\b(v?\d+\.\d+(\.\d+){0,2}([a-z0-9\.-]+)?)\b", re.IGNORECASE),
    re.compile(r"^\s*[a-z0-9_\-]+(\s+[a-z0-9_\-]+){0,3}\s+v?\d+\.\d+", re.IGNORECASE),
)

MARKET_INTEL_PATTERNS = (
    re.compile(r"\b(investment|funding|raised|series [a-z]|acquisition|acquire)\b", re.IGNORECASE),
    re.compile(r"\b(partnership|contract|deal|agreement|deployment|rollout)\b", re.IGNORECASE),
    re.compile(r"\b(artificial intelligence|machine learning|automation|ai)\b", re.IGNORECASE),
    re.compile(r"\b(expansion|launch|technology|platform)\b", re.IGNORECASE),
)


@dataclass(slots=True)
class NewsSyncSummary:
    """Summary counters for a refresh run."""

    companies_checked: int = 0
    articles_fetched: int = 0
    articles_created: int = 0
    articles_updated: int = 0
    articles_skipped: int = 0
    articles_duplicates: int = 0
    articles_rejected_irrelevant: int = 0
    companies_total: int = 0
    rotation_offset: int = 0
    rag_news_indexed: int = 0
    rag_indexing_status: str = "not_attempted"
    skip_reasons: dict[str, int] = field(
        default_factory=lambda: {reason: 0 for reason in sorted(SUPPORTED_SKIP_REASONS)}
    )

    def register_skip(self, reason: str) -> None:
        """Increment skip counters for a reason."""

        normalized_reason = reason if reason in SUPPORTED_SKIP_REASONS else SKIP_REASON_OTHER
        self.articles_skipped += 1
        self.skip_reasons[normalized_reason] = self.skip_reasons.get(normalized_reason, 0) + 1

        if normalized_reason in {SKIP_REASON_DUPLICATE_URL, SKIP_REASON_DUPLICATE_TITLE}:
            self.articles_duplicates += 1
        if normalized_reason in {SKIP_REASON_IRRELEVANT_CONTENT, SKIP_REASON_WEAK_COMPANY_MATCH}:
            self.articles_rejected_irrelevant += 1

    def to_dict(self) -> dict[str, int | str | dict[str, int]]:
        """Serialize summary metrics into a JSON-ready payload."""

        return {
            "companies_checked": self.companies_checked,
            "companies_total": self.companies_total,
            "rotation_offset": self.rotation_offset,
            "articles_fetched": self.articles_fetched,
            "articles_created": self.articles_created,
            "articles_updated": self.articles_updated,
            "articles_skipped": self.articles_skipped,
            "articles_duplicates": self.articles_duplicates,
            "articles_rejected_irrelevant": self.articles_rejected_irrelevant,
            "skip_reasons": self.skip_reasons,
            "rag_news_indexed": self.rag_news_indexed,
            "rag_indexing_status": self.rag_indexing_status,
        }


class NewsSyncService:
    """Fetch recent company-focused news from NewsAPI and persist it."""

    def __init__(
        self,
        session: Session,
        *,
        news_repository: NewsRepository | None = None,
        client: NewsApiClient | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.session = session
        self.news_repository = news_repository or NewsRepository(session)
        self.client = client or NewsApiClient()
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @staticmethod
    def _normalize_text(value: str | None) -> str:
        """Normalize text for matching and deduplication."""

        if not value:
            return ""
        normalized = value.lower().translate(str.maketrans("", "", string.punctuation))
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized.strip()

    @staticmethod
    def _normalize_company_name(value: str) -> str:
        """Normalize a company name while trimming common legal suffixes."""

        normalized = NewsSyncService._normalize_text(value)
        suffixes = (
            " ag",
            " se",
            " gmbh",
            " ltd",
            " llc",
            " inc",
            " corporation",
            " corp",
            " plc",
            " co",
            " company",
        )
        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[: -len(suffix)]
        return normalized.strip()

    @staticmethod
    def _normalize_published_at(value: Any) -> datetime:
        """Normalize publication timestamps into timezone-aware UTC values."""

        if isinstance(value, datetime):
            return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
        if isinstance(value, str) and value:
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        return datetime.now(timezone.utc)

    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract a normalized source domain."""

        try:
            return urlparse(url).netloc.lower().removeprefix("www.")
        except ValueError:
            return ""

    @staticmethod
    def _canonicalize_url(url: str) -> str:
        """Normalize URL by removing common tracking query parameters."""

        trimmed = url.strip()
        if not trimmed:
            return ""
        try:
            parsed = urlparse(trimmed)
        except ValueError:
            return trimmed

        cleaned_query = urlencode(
            sorted(
                [
                    (key, value)
                    for key, value in parse_qsl(parsed.query, keep_blank_values=True)
                    if key.lower() not in TRACKING_QUERY_PARAMS
                ]
            ),
            doseq=True,
        )
        cleaned_path = parsed.path.rstrip("/") or "/"
        return urlunparse(
            (
                parsed.scheme.lower(),
                parsed.netloc.lower(),
                cleaned_path,
                "",
                cleaned_query,
                "",
            )
        )

    def _log_skip(
        self,
        *,
        reason: str,
        company_name: str,
        article: dict[str, Any],
        detail: str | None = None,
    ) -> None:
        """Emit structured skip logs for auditability."""

        safe_reason = reason if reason in SUPPORTED_SKIP_REASONS else SKIP_REASON_OTHER
        title = str(article.get("title") or "").strip()
        url = str(article.get("url") or "").strip()
        self.logger.info(
            "Skipping news article during sync.",
            extra={
                "reason": safe_reason,
                "company": company_name,
                "title": title[:220],
                "url": url[:350],
                "source_domain": self._extract_domain(url),
                "detail": detail or "",
            },
        )

    def _count_companies(self) -> int:
        """Return total companies for sync planning."""

        return int(self.session.execute(select(func.count()).select_from(Company)).scalar_one())

    def _calculate_rotation_offset(self, *, total: int, limit: int) -> int:
        """Compute a stable cursor offset for safe sync rotation."""

        if total <= 0:
            return 0
        window_minutes = max(1, settings.NEWS_SYNC_ROTATION_WINDOW_MINUTES)
        window_size_seconds = window_minutes * 60
        window_index = int(datetime.now(timezone.utc).timestamp()) // window_size_seconds
        return int((window_index * limit) % total)

    def _load_companies_for_refresh(self, *, limit: int) -> tuple[list[Company], int, int]:
        """Load companies with rotation so repeated refreshes cover full dataset."""

        total_companies = self._count_companies()
        if total_companies == 0:
            return [], 0, 0

        effective_limit = min(limit, total_companies)
        offset = self._calculate_rotation_offset(total=total_companies, limit=effective_limit)

        primary_statement = (
            select(Company)
            .order_by(Company.vendor_name.asc())
            .offset(offset)
            .limit(effective_limit)
        )
        companies = list(self.session.execute(primary_statement).scalars().all())

        if len(companies) < effective_limit:
            remaining = effective_limit - len(companies)
            wrap_statement = select(Company).order_by(Company.vendor_name.asc()).limit(remaining)
            companies.extend(list(self.session.execute(wrap_statement).scalars().all()))

        return companies, total_companies, offset

    def _title_and_body_text(self, article: dict[str, Any]) -> tuple[str, str]:
        """Return normalized title and aggregate body text."""

        title = self._normalize_text(str(article.get("title") or ""))
        body = self._normalize_text(
            " ".join(
                [
                    str(article.get("description") or ""),
                    str(article.get("content") or ""),
                ]
            )
        )
        return title, body

    def _contains_market_intel_signal(self, article: dict[str, Any]) -> bool:
        """Return whether content looks like business or technology intelligence."""

        title_text, body_text = self._title_and_body_text(article)
        combined = f"{title_text} {body_text}".strip()
        if not combined:
            return False
        return any(pattern.search(combined) for pattern in MARKET_INTEL_PATTERNS)

    def _is_blocked_source_or_release_content(self, article: dict[str, Any], blocked_domains: set[str]) -> bool:
        """Reject low-value package/release style sources and titles."""

        url = str(article.get("url") or "")
        title = str(article.get("title") or "")
        domain = self._extract_domain(url)
        if domain in blocked_domains:
            return True
        if domain.endswith("github.com"):
            parsed = urlparse(url)
            path = parsed.path.lower()
            if "/releases" in path or "/tags/" in path:
                return True
        return any(pattern.search(title) for pattern in AUTOMATED_RELEASE_PATTERNS)

    def _company_match_strength(self, article: dict[str, Any], company: Company) -> str:
        """Classify match confidence between article text and company name."""

        normalized_company = self._normalize_company_name(company.vendor_name)
        if not normalized_company:
            return "none"

        title_text, body_text = self._title_and_body_text(article)
        if not title_text and not body_text:
            return "none"

        full_phrase = rf"\b{re.escape(normalized_company)}\b"
        if re.search(full_phrase, title_text):
            return "strong"
        if re.search(full_phrase, body_text):
            return "medium"

        tokens = [token for token in normalized_company.split(" ") if len(token) >= 3]
        if not tokens:
            return "none"
        if len(tokens) == 1 and tokens[0] in GENERIC_COMPANY_TOKENS:
            return "none"

        title_token_hits = sum(1 for token in tokens if re.search(rf"\b{re.escape(token)}\b", title_text))
        body_token_hits = sum(1 for token in tokens if re.search(rf"\b{re.escape(token)}\b", body_text))
        if title_token_hits >= 2:
            return "medium"
        if title_token_hits >= 1 and body_token_hits >= 1:
            return "medium"
        if body_token_hits >= 2:
            return "weak"
        return "none"

    def _find_existing_by_canonical_url(self, canonical_url: str) -> NewsArticle | None:
        """Locate existing article by canonical URL, including stored URL variants."""

        direct = self.news_repository.get_article_by_url(canonical_url)
        if direct is not None:
            return direct

        parsed = urlparse(canonical_url)
        url_prefix = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
        if not url_prefix:
            return None
        candidates = self.news_repository.get_articles_by_url_prefix(url_prefix)
        for candidate in candidates:
            if self._canonicalize_url(candidate.url) == canonical_url:
                return candidate
        return None

    def _upsert_article(
        self,
        *,
        company: Company,
        title: str,
        canonical_url: str,
        published_at: datetime,
    ) -> tuple[str, NewsArticle | None, str | None]:
        """Create or update an article using canonical URL then title/date dedupe."""

        existing_by_url = self._find_existing_by_canonical_url(canonical_url)
        if existing_by_url is not None:
            if existing_by_url.company_id != company.id:
                return "skipped", None, SKIP_REASON_CROSS_COMPANY_CONFLICT

            updated = False
            normalized_existing_title = self._normalize_text(existing_by_url.title)
            normalized_incoming_title = self._normalize_text(title)
            if normalized_existing_title != normalized_incoming_title:
                existing_by_url.title = title
                updated = True
            if existing_by_url.published_at != published_at:
                existing_by_url.published_at = published_at
                updated = True
            return ("updated", existing_by_url, None) if updated else ("skipped", None, SKIP_REASON_DUPLICATE_URL)

        existing_by_fallback = self.news_repository.get_article_by_title_and_published_at(
            title=title,
            published_at=published_at,
        )
        if existing_by_fallback is not None:
            if existing_by_fallback.company_id != company.id:
                return "skipped", None, SKIP_REASON_CROSS_COMPANY_CONFLICT
            return "skipped", None, SKIP_REASON_DUPLICATE_TITLE

        created = NewsArticle(
            company_id=company.id,
            title=title,
            url=canonical_url,
            published_at=published_at,
        )
        self.session.add(created)
        return "created", created, None

    def _index_news_updates(self, article_ids: list[UUID]) -> tuple[int, str]:
        """Incrementally index refreshed news rows into ChromaDB."""

        if not article_ids:
            return 0, "not_needed"

        ingestion_service = PostgresVectorIngestionService(session=self.session)
        try:
            indexed = ingestion_service.index_news_by_ids(article_ids)
        except (IndexingError, VectorStoreError):
            self.logger.exception("News refresh completed but ChromaDB incremental indexing failed.")
            return 0, "failed"
        return indexed, "indexed"

    @staticmethod
    def _parse_csv_setting(value: str) -> list[str]:
        """Parse comma-separated settings into normalized values."""

        return [entry.strip().lower() for entry in value.split(",") if entry.strip()]

    def refresh_latest_news(
        self,
        *,
        company_limit: int | None = None,
        lookback_days: int | None = None,
        page_size: int | None = None,
    ) -> NewsSyncSummary:
        """Refresh latest persisted news using company-focused NewsAPI queries."""

        effective_company_limit = company_limit or settings.NEWS_SYNC_MAX_COMPANIES_PER_REFRESH
        effective_lookback_days = lookback_days or settings.NEWS_SYNC_LOOKBACK_DAYS
        effective_page_size = page_size or settings.NEWS_SYNC_PAGE_SIZE

        from_date = datetime.now(timezone.utc) - timedelta(days=max(1, effective_lookback_days))
        companies, total_companies, rotation_offset = self._load_companies_for_refresh(
            limit=max(1, effective_company_limit)
        )

        summary = NewsSyncSummary(
            companies_checked=len(companies),
            companies_total=total_companies,
            rotation_offset=rotation_offset,
        )
        blocked_domains = set(self._parse_csv_setting(settings.NEWS_SYNC_BLOCKED_DOMAINS))
        market_keywords = self._parse_csv_setting(settings.NEWS_SYNC_MARKET_KEYWORDS)

        seen_urls: set[str] = set()
        changed_article_ids: list[UUID] = []

        for company in companies:
            articles = self.client.fetch_company_news(
                company.vendor_name,
                from_date=from_date,
                page_size=max(1, effective_page_size),
                market_keywords=market_keywords,
            )
            summary.articles_fetched += len(articles)

            for article in articles:
                title = str(article.get("title") or "").strip()
                raw_url = str(article.get("url") or "").strip()
                canonical_url = self._canonicalize_url(raw_url)

                if not title or not canonical_url:
                    summary.register_skip(SKIP_REASON_INVALID_ARTICLE)
                    self._log_skip(
                        reason=SKIP_REASON_INVALID_ARTICLE,
                        company_name=company.vendor_name,
                        article=article,
                    )
                    continue

                if canonical_url in seen_urls:
                    summary.register_skip(SKIP_REASON_DUPLICATE_URL)
                    self._log_skip(
                        reason=SKIP_REASON_DUPLICATE_URL,
                        company_name=company.vendor_name,
                        article=article,
                        detail="in_batch_duplicate",
                    )
                    continue

                if self._is_blocked_source_or_release_content(article, blocked_domains):
                    summary.register_skip(SKIP_REASON_IRRELEVANT_CONTENT)
                    self._log_skip(
                        reason=SKIP_REASON_IRRELEVANT_CONTENT,
                        company_name=company.vendor_name,
                        article=article,
                        detail="blocked_source_or_release_pattern",
                    )
                    continue

                match_strength = self._company_match_strength(article, company)
                if match_strength not in {"strong", "medium"}:
                    summary.register_skip(SKIP_REASON_WEAK_COMPANY_MATCH)
                    self._log_skip(
                        reason=SKIP_REASON_WEAK_COMPANY_MATCH,
                        company_name=company.vendor_name,
                        article=article,
                        detail=f"match_strength={match_strength}",
                    )
                    continue

                if not self._contains_market_intel_signal(article):
                    summary.register_skip(SKIP_REASON_IRRELEVANT_CONTENT)
                    self._log_skip(
                        reason=SKIP_REASON_IRRELEVANT_CONTENT,
                        company_name=company.vendor_name,
                        article=article,
                        detail="missing_market_intelligence_signal",
                    )
                    continue

                published_at = self._normalize_published_at(article.get("published_at"))
                action, entity, skip_reason = self._upsert_article(
                    company=company,
                    title=title,
                    canonical_url=canonical_url,
                    published_at=published_at,
                )
                seen_urls.add(canonical_url)

                if action == "created" and entity is not None:
                    summary.articles_created += 1
                    changed_article_ids.append(entity.id)
                    continue
                if action == "updated" and entity is not None:
                    summary.articles_updated += 1
                    changed_article_ids.append(entity.id)
                    continue

                resolved_reason = skip_reason or SKIP_REASON_OTHER
                summary.register_skip(resolved_reason)
                self._log_skip(
                    reason=resolved_reason,
                    company_name=company.vendor_name,
                    article=article,
                )

        self.session.commit()

        indexed_count, indexing_status = self._index_news_updates(changed_article_ids)
        summary.rag_news_indexed = indexed_count
        summary.rag_indexing_status = indexing_status

        self.logger.info("News refresh completed.", extra=summary.to_dict())
        return summary

    def reindex_all_persisted_news(self) -> dict[str, int | str]:
        """Rebuild the complete news portion of the ChromaDB index.

        Existing news vectors are deleted first so stale vectors belonging
        to deleted PostgreSQL records cannot remain in semantic retrieval.

        Company, problem, and sector vectors are preserved.

        Returns:
            dict[str, int | str]: Reindex operation summary.
        """

        self.logger.info(
            "Starting full persisted-news ChromaDB reindex."
        )

        vector_store = ChromaVectorStoreService()

        # ---------------------------------------------------------
        # Step 1: Delete ALL existing news vectors from ChromaDB.
        # ---------------------------------------------------------

        try:
            stale_vectors_deleted = (
                vector_store.delete_by_entity_type(
                    entity_type="news"
                )
            )

        except VectorStoreError as exc:
            self.logger.exception(
                "Failed to clear existing news vectors "
                "before reindex."
            )

            raise IndexingError(
                "Failed to remove existing news vectors "
                "from ChromaDB before reindexing."
            ) from exc

        self.logger.info(
            "Removed %s existing news vector(s) "
            "from ChromaDB.",
            stale_vectors_deleted,
        )

        # ---------------------------------------------------------
        # Step 2: Load current PostgreSQL news records.
        # ---------------------------------------------------------

        news_ids = (
            self.news_repository
            .get_all_article_ids()
        )

        records_found = len(news_ids)

        # ---------------------------------------------------------
        # Step 3: Handle empty PostgreSQL news table.
        #
        # This is important:
        # Even when PostgreSQL contains zero news records,
        # stale Chroma news vectors have already been removed.
        # ---------------------------------------------------------

        if records_found == 0:
            self.logger.info(
                "No persisted news records found. "
                "News vectors were cleared successfully."
            )

            return {
                "status": "empty",
                "stale_news_vectors_deleted": (
                    stale_vectors_deleted
                ),
                "news_records_found": 0,
                "news_records_indexed": 0,
                "news_chunks_indexed": 0,
            }

        # ---------------------------------------------------------
        # Step 4: Reindex current PostgreSQL records.
        # ---------------------------------------------------------

        ingestion_service = (
            PostgresVectorIngestionService(
                session=self.session,
                vector_store=vector_store,
            )
        )

        try:
            indexed_chunks = (
                ingestion_service
                .index_news_by_ids(news_ids)
            )

        except (IndexingError, VectorStoreError) as exc:
            self.logger.exception(
                "Failed to rebuild news vectors "
                "after clearing stale vectors."
            )

            raise IndexingError(
                "Existing news vectors were cleared, "
                "but rebuilding the news index failed."
            ) from exc

        self.logger.info(
            "News ChromaDB reindex completed. "
            "stale_deleted=%s records_found=%s "
            "chunks_indexed=%s",
            stale_vectors_deleted,
            records_found,
            indexed_chunks,
        )

        return {
            "status": "indexed",
            "stale_news_vectors_deleted": (
                stale_vectors_deleted
            ),
            "news_records_found": records_found,
            "news_records_indexed": records_found,
            "news_chunks_indexed": indexed_chunks,
        }


__all__ = [
    "NewsSyncService",
    "NewsSyncSummary",
    "NewsApiAuthenticationError",
    "NewsApiConfigurationError",
    "NewsApiRateLimitError",
    "NewsApiRequestError",
    "NewsApiResponseError",
]
