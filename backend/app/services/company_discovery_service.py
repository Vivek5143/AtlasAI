"""Company discovery workflow services."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import logging
import re
import string
from typing import Protocol
from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai import IndexingError, VectorStoreError
from app.clients.news_api_client import (
    NewsApiAuthenticationError,
    NewsApiClient,
    NewsApiConfigurationError,
    NewsApiRateLimitError,
    NewsApiRequestError,
    NewsApiResponseError,
)
from app.models.company import Company
from app.models.company_discovery_candidate import (
    CompanyDiscoveryCandidate,
    CompanyDiscoveryStatus,
)
from app.repositories.company_discovery_repository import CompanyDiscoveryRepository
from app.services.company_service import CompanyService
from app.utils.datetime import utc_now


class DiscoveryError(Exception):
    """Base class for discovery workflow errors."""


class DiscoveryProviderConfigurationError(DiscoveryError):
    """Raised when no discovery provider is configured."""


class DiscoveryProviderAuthenticationError(DiscoveryError):
    """Raised when the discovery provider rejects credentials."""


class DiscoveryProviderRateLimitError(DiscoveryError):
    """Raised when the discovery provider is rate limited."""


class DiscoveryProviderRequestError(DiscoveryError):
    """Raised when the discovery provider cannot be reached."""


class DiscoveryProviderResponseError(DiscoveryError):
    """Raised when the discovery provider returns invalid data."""


class DiscoveryValidationError(DiscoveryError):
    """Raised when a candidate cannot pass deterministic validation."""


class CandidateReviewStateError(DiscoveryError):
    """Raised when a reviewed candidate is reviewed again."""


class DuplicateCompanyError(DiscoveryError):
    """Raised when a candidate duplicates an existing trusted company."""


@dataclass(slots=True)
class DiscoveryProviderCandidate:
    """Candidate data returned by an external discovery provider."""

    company_name: str
    evidence_url: str
    evidence_title: str | None = None
    evidence_text: str | None = None
    website: str | None = None
    country: str | None = None
    description: str | None = None
    ai_category: str | None = None
    provider: str = "tavily"
    provider_company_id: str | None = None
    provider_metadata: dict | None = None


@dataclass(slots=True)
class DiscoverySkippedCandidate:
    """Audit detail for a skipped discovery result."""

    company_name: str | None
    evidence_url: str | None
    reason: str


@dataclass(slots=True)
class ProviderExtractionDetail:
    """Safe provider extraction diagnostic for a skipped article."""

    title: str | None
    source_domain: str | None
    extraction_skip_reason: str


@dataclass(slots=True)
class DiscoveryRunSummary:
    """Summary returned after a discovery search."""

    candidates_found: int = 0
    candidates_created: int = 0
    candidates_skipped: int = 0
    articles_fetched: int = 0
    provider_candidates_extracted: int = 0
    provider_extraction_skipped: int = 0
    items: list[CompanyDiscoveryCandidate] = field(default_factory=list)
    skipped: list[DiscoverySkippedCandidate] = field(default_factory=list)
    provider_extraction_details: list[ProviderExtractionDetail] = field(default_factory=list)


@dataclass(slots=True)
class ProviderDiscoveryStats:
    """Provider-level extraction counters for discovery observability."""

    articles_fetched: int = 0
    candidates_extracted: int = 0
    missing_url: int = 0
    no_company_name_extracted: int = 0
    blocked_generic_name: int = 0
    unrelated_article: int = 0
    irrelevant_candidate: int = 0
    provider_duplicate: int = 0
    extraction_details: list[ProviderExtractionDetail] = field(default_factory=list)

    @property
    def extraction_skipped(self) -> int:
        """Return total provider-side skips before verification."""

        return (
            self.missing_url
            + self.no_company_name_extracted
            + self.blocked_generic_name
            + self.unrelated_article
            + self.irrelevant_candidate
            + self.provider_duplicate
        )

    @property
    def skipped_missing_url(self) -> int:
        """Backward-compatible alias for provider missing URL skips."""

        return self.missing_url

    @property
    def skipped_name_not_extracted(self) -> int:
        """Backward-compatible alias for extraction misses."""

        return self.no_company_name_extracted

    @property
    def skipped_duplicates(self) -> int:
        """Backward-compatible alias for duplicate provider signals."""

        return self.provider_duplicate


class CompanyDiscoveryProvider(Protocol):
    """Interface for external company discovery providers."""

    def discover(
        self,
        *,
        query: str | None,
        sector: str | None,
        country: str | None,
        limit: int,
    ) -> list[DiscoveryProviderCandidate]:
        """Return externally evidenced company candidates."""


class CompanyIndexingService(Protocol):
    """Interface for focused company indexing."""

    def index_company_by_id(self, company_id: UUID) -> int:
        """Index a single approved company."""


class NewsApiCompanyDiscoveryProvider:
    """NewsAPI-backed discovery provider using articles as discovery signals."""

    DISCOVERY_EXCLUDED_DOMAINS = ("abcnews.go.com",)
    DIAGNOSTIC_TITLE_MAX_LENGTH = 180
    NAME_WORD_PATTERN = (
        r"(?:[A-ZÀ-ÖØ-Þ0-9][A-Za-zÀ-ÖØ-öø-ÿ0-9&.'\-]*|"
        r"[a-z][A-Za-z0-9]*[A-Z][A-Za-z0-9]*)"
    )
    COMPANY_NAME_PATTERN = rf"{NAME_WORD_PATTERN}(?:\s+{NAME_WORD_PATTERN}){{0,5}}"
    AI_QUERY_PATTERN = re.compile(
        r"\b(ai|artificial intelligence|machine learning|ml|automation|"
        r"generative ai|computer vision|nlp|robotics)\b",
        re.IGNORECASE,
    )
    QUERY_STOP_WORDS = {
        "and",
        "for",
        "from",
        "into",
        "near",
        "the",
        "with",
    }
    TECHNOLOGY_QUERY_TERMS = {
        "ai",
        "artificial intelligence",
        "automation",
        "computer vision",
        "generative ai",
        "machine learning",
        "ml",
        "nlp",
        "predictive analytics",
        "robotics",
    }
    ORGANIZATION_QUERY_TERMS = {
        "company",
        "platform",
        "software",
        "startup",
        "technology",
        "vendor",
    }
    GENERIC_NAME_WORDS = {
        "ai",
        "analysis",
        "artificial",
        "ask",
        "category",
        "company",
        "exclusive",
        "food",
        "forecast",
        "german",
        "global",
        "hn",
        "industry",
        "intelligence",
        "latest",
        "live",
        "learning",
        "manufacturer",
        "manufacturing",
        "market",
        "new",
        "news",
        "opinion",
        "platform",
        "report",
        "research",
        "sector",
        "show",
        "software",
        "startup",
        "study",
        "technology",
        "update",
        "updates",
        "vendor",
        "video",
        "watch",
    }
    GENERIC_LEADING_WORDS = {
        "the",
    }
    EXTRACTION_BLOCKLIST = {
        "abc news",
        "analysis",
        "ask hn",
        "breaking",
        "cbs news",
        "download",
        "exclusive",
        "fox news",
        "live",
        "latest",
        "latest news",
        "nbc news",
        "news",
        "opinion",
        "report",
        "show",
        "show hn",
        "the download",
        "the latest",
        "update",
        "updates",
        "video",
        "watch",
    }
    UPPERCASE_COMPANY_ALLOWLIST = {
        "ABB",
        "AMD",
        "ARM",
        "AWS",
        "BMW",
        "BYD",
        "GE",
        "HP",
        "IBM",
        "LG",
        "NVIDIA",
        "SAP",
        "TSMC",
    }
    INVALID_NAME_PHRASES = {
        "ai",
        "artificial intelligence",
        "machine learning",
        "new ai",
        "new ai platform",
        "ai platform",
        "ai technology",
        "food manufacturing",
        "german food manufacturer",
    }
    DISCOVERY_PATTERNS = (
        re.compile(
            rf"^\s*({COMPANY_NAME_PATTERN})\s+"
            r"(raises|raised|launches|launched|unveils|announces|announced|"
            r"partners|partnered|acquires|acquired|secures|secured|introduces|"
            r"develops|deploys|expands|builds)\b",
        ),
        re.compile(
            r"\b(?:startup|company|vendor|platform)\s+"
            rf"({COMPANY_NAME_PATTERN})\s+"
            r"(?:raises|launches|unveils|announces|partners|secures|introduces|develops)\b",
        ),
        re.compile(
            rf"^\s*({COMPANY_NAME_PATTERN})\s+"
            r"(?:uses|used|adopts|adopted|applies|applied|deploys|deployed)\s+"
            r"(?:AI|artificial intelligence|machine learning|automation|computer vision)\b",
        ),
        re.compile(
            r"\b(?:adopts|adopted|deploys|deployed|uses|used|implements|implemented|"
            r"selects|selected|integrates|integrated)\s+"
            r"(?:technology|platform|software|solutions?|systems?\s+)?"
            r"(?:(?:from|by)\s+)?"
            rf"({COMPANY_NAME_PATTERN})\s+"
            r"(?:AI|artificial intelligence|machine learning|automation|computer vision|"
            r"technology|platform|software|solution)\b",
        ),
        re.compile(
            r"\b(?:from|by)\s+"
            rf"({COMPANY_NAME_PATTERN})"
            r"(?=\s+(?:improves|improved|for|to|with|in|on|at|that|which|is|are|"
            r"has|have|will|can|could|aims|targets)\b|[,.:;!?]|$)",
        ),
        re.compile(rf"^\s*({COMPANY_NAME_PATTERN})\s*:\s+"),
        re.compile(rf"^\s*How\s+({COMPANY_NAME_PATTERN})\s+(?:is|are)\s+"),
        re.compile(
            r"\b(?:startup|company|vendor)\s+(?:called|named|known as)\s+"
            rf"({COMPANY_NAME_PATTERN})\b",
        ),
    )
    DESCRIPTION_DISCOVERY_PATTERNS = (
        re.compile(
            rf"\b({COMPANY_NAME_PATTERN})\s+"
            r"(?:uses|used|adopts|adopted|develops|developed|deploys|deployed|"
            r"launches|launched|offers|introduced|introduces)\s+"
            r"(?:AI|artificial intelligence|machine learning|automation|computer vision|"
            r"technology|software|platform|solution)\b",
        ),
        re.compile(
            r"\b(?:AI|artificial intelligence|machine learning|automation|computer vision)\s+"
            r"(?:platform|software|technology|solution)\s+(?:from|by)\s+"
            rf"({COMPANY_NAME_PATTERN})\b",
        ),
        re.compile(
            r"\b(?:startup|company|vendor)\s+(?:called|named|known as)\s+"
            rf"({COMPANY_NAME_PATTERN})\b",
        ),
    )
    EXPLICIT_ORGANIZATION_PATTERNS = (
        re.compile(
            r"\b(?i:(?:(?:AI|artificial intelligence|technology|tech|software|robotics)\s+"
            r"(?:startup|company|vendor)|startup|company|vendor))\s+"
            r"(?!(?i:called|named|known as)\b)"
            rf"({COMPANY_NAME_PATTERN})"
            r"(?=\s+(?:came|comes|emerged|emerges|launched|launches|announced|announces|"
            r"raised|raises|secured|secures|unveiled|unveils|developed|develops|built|"
            r"builds|offers|introduced|introduces|is|has|will|with|from|for|to|that|"
            r"which)\b|[,.:;!?]|$)",
        ),
    )

    def __init__(
        self,
        client: NewsApiClient | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.client = client or NewsApiClient()
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.last_stats = ProviderDiscoveryStats()

    @classmethod
    def _query_terms(cls, value: str | None) -> list[str]:
        """Return compact NewsAPI query terms from free-form input."""

        if not value:
            return []

        lowered = value.lower()
        terms: list[str] = []
        phrase_words: set[str] = set()
        for phrase in (
            "artificial intelligence",
            "machine learning",
            "generative ai",
            "computer vision",
            "food manufacturing",
            "predictive analytics",
        ):
            if phrase in lowered:
                terms.append(phrase)
                phrase_words.update(phrase.split())

        for token in re.findall(r"[A-Za-z0-9][A-Za-z0-9\-]{1,}", value):
            normalized = token.lower()
            if normalized in cls.QUERY_STOP_WORDS:
                continue
            if normalized in phrase_words:
                continue
            if len(normalized) < 3 and normalized not in {"ai", "ml"}:
                continue
            terms.append(token)

        deduped: list[str] = []
        seen: set[str] = set()
        for term in terms:
            key = term.lower()
            if key not in seen:
                seen.add(key)
                deduped.append(term)
        return deduped

    @staticmethod
    def _format_query_term(term: str) -> str:
        """Quote multi-word terms while preserving simple NewsAPI boolean syntax."""

        stripped = term.strip()
        if not stripped:
            return ""
        if re.search(r"\b(AND|OR|NOT)\b", stripped, re.IGNORECASE):
            return f"({stripped})"
        if re.search(r"\s", stripped):
            return f"\"{stripped}\""
        return stripped

    @classmethod
    def _build_query(
        cls,
        *,
        query: str | None,
        sector: str | None,
        country: str | None,
    ) -> str:
        del country

        query_terms = cls._query_terms(query)
        context_terms = list(query_terms)
        if sector and sector.strip():
            context_terms.extend(
                term
                for term in cls._query_terms(sector)
                if term.lower() not in {existing.lower() for existing in context_terms}
            )

        if not context_terms:
            context_terms = ["AI", "startup", "company"]

        formatted_context = [
            formatted
            for term in context_terms[:12]
            if (formatted := cls._format_query_term(term))
        ]
        context_query = " OR ".join(formatted_context)

        tech_terms = [
            term
            for term in context_terms
            if term.lower() in cls.TECHNOLOGY_QUERY_TERMS
            or cls.AI_QUERY_PATTERN.fullmatch(term.strip())
        ]
        industry_terms = [
            term
            for term in context_terms
            if term.lower() not in cls.TECHNOLOGY_QUERY_TERMS
            and term.lower() not in cls.ORGANIZATION_QUERY_TERMS
        ]
        organization_query = "(startup OR company OR vendor OR technology OR platform OR software)"
        exclusion_query = "NOT (watch OR video OR live OR updates)"

        if tech_terms and industry_terms:
            tech_query = " OR ".join(cls._format_query_term(term) for term in tech_terms[:6])
            industry_query = " OR ".join(cls._format_query_term(term) for term in industry_terms[:8])
            return f"(({tech_query}) AND ({industry_query}) AND {organization_query}) AND {exclusion_query}"

        if tech_terms:
            tech_query = " OR ".join(cls._format_query_term(term) for term in tech_terms[:6])
            return f"(({tech_query}) AND {organization_query}) AND {exclusion_query}"

        combined_input = " ".join(value for value in (query, sector) if value)
        if cls.AI_QUERY_PATTERN.search(combined_input):
            return f"({context_query}) AND {exclusion_query}"

        return (
            f"({context_query}) AND "
            "(AI OR \"artificial intelligence\" OR \"machine learning\" OR automation "
            "OR \"generative AI\" OR \"computer vision\" OR technology OR software OR platform) "
            f"AND {exclusion_query}"
        )

    @classmethod
    def _clean_extracted_name(cls, value: str | None) -> str | None:
        """Clean a deterministic company-name extraction."""

        if not value:
            return None

        name = re.sub(r"\s+", " ", value).strip(" .,'\"“”‘’:-")
        if not 2 <= len(name) <= 100:
            return None
        if len(name.split()) > 6:
            return None

        return name

    @classmethod
    def _is_blocked_extracted_name(cls, name: str) -> bool:
        """Return whether an extracted name is an editorial label or generic phrase."""

        normalized = name.lower().translate(str.maketrans("", "", string.punctuation))
        normalized = re.sub(r"\s+", " ", normalized).strip()
        if normalized in cls.EXTRACTION_BLOCKLIST or normalized in cls.INVALID_NAME_PHRASES:
            return True
        if normalized.endswith(" news"):
            return True

        uppercase_name = re.sub(r"[^A-Za-z0-9]+", "", name)
        if uppercase_name and uppercase_name == uppercase_name.upper():
            return name.strip().upper() not in cls.UPPERCASE_COMPANY_ALLOWLIST

        tokens = normalized.split()
        while tokens and tokens[0] in cls.GENERIC_LEADING_WORDS:
            tokens.pop(0)
        if tokens and all(token in cls.GENERIC_NAME_WORDS for token in tokens):
            return True
        meaningful_tokens = [token for token in tokens if token not in cls.GENERIC_NAME_WORDS and len(token) >= 2]
        return not meaningful_tokens

    @classmethod
    def _truncate_diagnostic_title(cls, title: str | None) -> str | None:
        """Return a bounded article title for provider diagnostics."""

        if not title:
            return None
        cleaned = re.sub(r"\s+", " ", title).strip()
        if len(cleaned) <= cls.DIAGNOSTIC_TITLE_MAX_LENGTH:
            return cleaned
        return cleaned[: cls.DIAGNOSTIC_TITLE_MAX_LENGTH - 3].rstrip() + "..."

    def _record_extraction_skip(
        self,
        stats: ProviderDiscoveryStats,
        *,
        title: str | None,
        source_domain: str | None,
        rule_attempted: str,
        reason: str,
    ) -> None:
        """Record safe diagnostics and structured logs for provider extraction skips."""

        detail = ProviderExtractionDetail(
            title=self._truncate_diagnostic_title(title),
            source_domain=source_domain or None,
            extraction_skip_reason=reason,
        )
        stats.extraction_details.append(detail)
        self.logger.info(
            "NewsAPI discovery article skipped during extraction.",
            extra={
                "article_title": title,
                "source_domain": source_domain,
                "extraction_rule_attempted": rule_attempted,
                "extraction_skip_reason": reason,
            },
        )

    @classmethod
    def _extract_company_name_from_text(
        cls,
        value: str | None,
        patterns: tuple[re.Pattern[str], ...],
    ) -> tuple[str | None, str | None]:
        """Return extracted company name and optional provider skip reason."""

        if not value:
            return None, "no_company_name_extracted"

        cleaned = re.split(r"\s+-\s+|\s+\|\s+", value, maxsplit=1)[0].strip()
        for pattern in patterns:
            match = pattern.search(cleaned)
            if match:
                name = cls._clean_extracted_name(match.group(1))
                if not name:
                    return None, "blocked_generic_name"
                if cls._is_blocked_extracted_name(name):
                    return None, "blocked_generic_name"
                return name, None
        return None, "no_company_name_extracted"

    @classmethod
    def _extract_company_name_with_reason(
        cls,
        title: str | None,
        description: str | None = None,
    ) -> tuple[str | None, str | None]:
        """Extract a company name, preferring explicit organization phrases."""

        for value in (description, title):
            name, reason = cls._extract_company_name_from_text(value, cls.EXPLICIT_ORGANIZATION_PATTERNS)
            if name or reason == "blocked_generic_name":
                return name, reason

        name, reason = cls._extract_company_name_from_text(title, cls.DISCOVERY_PATTERNS)
        if name or reason == "blocked_generic_name":
            return name, reason
        return cls._extract_company_name_from_text(description, cls.DESCRIPTION_DISCOVERY_PATTERNS)

    @classmethod
    def _extract_company_name(cls, title: str | None, description: str | None = None) -> str | None:
        name, _ = cls._extract_company_name_with_reason(title, description)
        return name

    def discover(
        self,
        *,
        query: str | None,
        sector: str | None,
        country: str | None,
        limit: int,
    ) -> list[DiscoveryProviderCandidate]:
        """Fetch NewsAPI articles and extract evidenced company names."""

        from_date = datetime.now(timezone.utc) - timedelta(days=30)
        search_query = self._build_query(query=query, sector=sector, country=country)
        self.last_stats = ProviderDiscoveryStats()
        self.logger.info(
            "NewsAPI discovery query built.",
            extra={"query": search_query},
        )
        try:
            articles = self.client.fetch_everything(
                search_query,
                from_date=from_date,
                page_size=max(1, min(limit * 3, 100)),
                sort_by="relevancy",
                search_in="title,description,content",
                exclude_domains=list(self.DISCOVERY_EXCLUDED_DOMAINS),
            )
        except NewsApiConfigurationError as exc:
            raise DiscoveryProviderConfigurationError(str(exc)) from exc
        except NewsApiAuthenticationError as exc:
            raise DiscoveryProviderAuthenticationError(str(exc)) from exc
        except NewsApiRateLimitError as exc:
            raise DiscoveryProviderRateLimitError(str(exc)) from exc
        except NewsApiRequestError as exc:
            raise DiscoveryProviderRequestError(str(exc)) from exc
        except NewsApiResponseError as exc:
            raise DiscoveryProviderResponseError(str(exc)) from exc

        candidates: list[DiscoveryProviderCandidate] = []
        seen: set[tuple[str, str]] = set()
        stats = ProviderDiscoveryStats(articles_fetched=len(articles))
        for article in articles:
            title = str(article.get("title") or "").strip()
            description = str(article.get("description") or "").strip()
            url = str(article.get("url") or "").strip()
            source_domain = CompanyVerificationService.extract_domain(url)
            if not url:
                stats.missing_url += 1
                self._record_extraction_skip(
                    stats,
                    title=title,
                    source_domain=None,
                    rule_attempted="url_required",
                    reason="missing_url",
                )
                continue
            if source_domain in self.DISCOVERY_EXCLUDED_DOMAINS:
                stats.unrelated_article += 1
                self._record_extraction_skip(
                    stats,
                    title=title,
                    source_domain=source_domain,
                    rule_attempted="excluded_domain_filter",
                    reason="unrelated_article",
                )
                continue
            company_name, extraction_skip_reason = self._extract_company_name_with_reason(title, description)
            if not company_name:
                if extraction_skip_reason == "blocked_generic_name":
                    stats.blocked_generic_name += 1
                else:
                    stats.no_company_name_extracted += 1
                self._record_extraction_skip(
                    stats,
                    title=title,
                    source_domain=source_domain,
                    rule_attempted="title_then_description_patterns",
                    reason=extraction_skip_reason or "no_company_name_extracted",
                )
                continue
            key = (company_name.lower(), url.lower())
            if key in seen:
                stats.provider_duplicate += 1
                self._record_extraction_skip(
                    stats,
                    title=title,
                    source_domain=source_domain,
                    rule_attempted="provider_candidate_dedupe",
                    reason="provider_duplicate",
                )
                continue
            seen.add(key)
            if len(candidates) < limit:
                candidates.append(
                    DiscoveryProviderCandidate(
                        company_name=company_name,
                        evidence_url=url,
                        evidence_title=title,
                        evidence_text=" ".join(
                            str(article.get(field_name) or "").strip()
                            for field_name in ("description", "content")
                            if article.get(field_name)
                        )
                        or None,
                        description=str(article.get("description") or "").strip() or None,
                    )
                )

        stats.candidates_extracted = len(candidates)
        self.last_stats = stats
        self.logger.info(
            "NewsAPI discovery completed.",
            extra={
                "query": search_query,
                "articles_fetched": stats.articles_fetched,
                "candidates_extracted": stats.candidates_extracted,
                "missing_url": stats.missing_url,
                "no_company_name_extracted": stats.no_company_name_extracted,
                "blocked_generic_name": stats.blocked_generic_name,
                "provider_duplicate": stats.provider_duplicate,
            },
        )
        return candidates


class CompanyVerificationService:
    """Deterministic validation, scoring, and duplicate checks."""

    AI_TECH_PATTERNS = (
        re.compile(r"\b(ai|artificial intelligence|machine learning|ml|automation)\b", re.IGNORECASE),
        re.compile(r"\b(generative ai|computer vision|nlp|data platform|predictive analytics)\b", re.IGNORECASE),
        re.compile(r"\b(software|technology|platform|cloud|robotics|agentic)\b", re.IGNORECASE),
    )
    LOW_QUALITY_PATTERNS = (
        re.compile(r"\b(pypi|npm|package|github release|changelog|version bump|release notes)\b", re.IGNORECASE),
        re.compile(r"\b(market report|market size|forecast period|sample report|research report)\b", re.IGNORECASE),
        re.compile(r"\b(coupon|casino|adult|betting|torrent)\b", re.IGNORECASE),
    )
    CREDIBLE_SOURCE_DOMAINS = {
        "techcrunch.com",
        "venturebeat.com",
        "theinformation.com",
        "reuters.com",
        "businesswire.com",
        "prnewswire.com",
        "globenewswire.com",
        "forbes.com",
        "zdnet.com",
        "thenextweb.com",
    }
    BLOCKED_DOMAINS = {"github.com", "pypi.org", "npmjs.com", "registry.npmjs.org"}
    LEGAL_SUFFIXES = (
        "incorporated",
        "corporation",
        "company",
        "corp",
        "inc",
        "llc",
        "ltd",
        "limited",
        "gmbh",
        "plc",
        "ag",
        "co",
    )

    def __init__(self, session: Session, logger: logging.Logger | None = None) -> None:
        self.session = session
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @staticmethod
    def normalize_name(value: str | None) -> str:
        """Normalize names for duplicate detection and matching."""

        if not value:
            return ""
        normalized = value.lower().translate(str.maketrans("", "", string.punctuation))
        normalized = re.sub(r"\s+", " ", normalized).strip()
        parts = normalized.split()
        while parts and parts[-1] in CompanyVerificationService.LEGAL_SUFFIXES:
            parts.pop()
        return " ".join(parts).strip()

    @staticmethod
    def extract_domain(url: str | None) -> str:
        """Return a normalized domain from a URL."""

        if not url:
            return ""
        try:
            parsed = urlparse(url.strip())
        except ValueError:
            return ""
        return parsed.netloc.lower().removeprefix("www.")

    @staticmethod
    def is_valid_url(url: str | None) -> bool:
        """Return whether a URL has a valid HTTP(S) shape."""

        if not url:
            return False
        try:
            parsed = urlparse(url.strip())
        except ValueError:
            return False
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

    def _combined_evidence_text(self, candidate: DiscoveryProviderCandidate) -> str:
        return " ".join(
            value
            for value in (
                candidate.evidence_title,
                candidate.evidence_text,
                candidate.description,
                candidate.ai_category,
            )
            if value
        )

    def _name_match_strength(self, candidate: DiscoveryProviderCandidate) -> str:
        normalized_name = self.normalize_name(candidate.company_name)
        text = self.normalize_name(self._combined_evidence_text(candidate))
        if not normalized_name or not text:
            return "none"
        if re.search(rf"\b{re.escape(normalized_name)}\b", text):
            return "strong"
        tokens = [token for token in normalized_name.split() if len(token) >= 3]
        if not tokens:
            return "none"
        hits = sum(1 for token in tokens if re.search(rf"\b{re.escape(token)}\b", text))
        if hits >= min(2, len(tokens)):
            return "medium"
        if hits == 1 and len(tokens) == 1:
            return "weak"
        return "none"

    def _has_ai_technology_relevance(self, candidate: DiscoveryProviderCandidate) -> bool:
        text = self._combined_evidence_text(candidate)
        return any(pattern.search(text) for pattern in self.AI_TECH_PATTERNS)

    def _is_low_quality(self, candidate: DiscoveryProviderCandidate) -> bool:
        domain = self.extract_domain(candidate.evidence_url)
        text = self._combined_evidence_text(candidate)
        return domain in self.BLOCKED_DOMAINS or any(
            pattern.search(text) for pattern in self.LOW_QUALITY_PATTERNS
        )

    def validate_and_score(
        self,
        candidate: DiscoveryProviderCandidate,
    ) -> tuple[float, list[str]]:
        """Validate a provider candidate and return a transparent score."""

        reasons: list[str] = []
        score = 0.0

        if not candidate.company_name or not candidate.company_name.strip():
            raise DiscoveryValidationError("missing_company_name")
        if not self.is_valid_url(candidate.evidence_url):
            raise DiscoveryValidationError("invalid_or_missing_evidence_url")
        if candidate.website and not self.is_valid_url(candidate.website):
            raise DiscoveryValidationError("invalid_website")
        if self._is_low_quality(candidate):
            raise DiscoveryValidationError("low_quality_or_package_release_content")

        source_domain = self.extract_domain(candidate.evidence_url)
        name_strength = self._name_match_strength(candidate)
        if name_strength == "strong":
            score += 0.30
            reasons.append("strong company-name match in evidence")
        elif name_strength == "medium":
            score += 0.20
            reasons.append("partial company-name match in evidence")
        else:
            raise DiscoveryValidationError("company_name_not_relevant_to_evidence")

        if self._has_ai_technology_relevance(candidate):
            score += 0.25
            reasons.append("evidence contains AI or technology relevance")
        else:
            raise DiscoveryValidationError("missing_ai_technology_relevance")

        if candidate.website:
            score += 0.15
            reasons.append("official website provided")
        else:
            reasons.append("official website not provided")

        if source_domain in self.CREDIBLE_SOURCE_DOMAINS:
            score += 0.15
            reasons.append(f"credible evidence source: {source_domain}")
        else:
            score += 0.05
            reasons.append(f"external evidence source: {source_domain}")

        if candidate.description and len(candidate.description.strip()) >= 60:
            score += 0.10
            reasons.append("substantive evidence description provided")

        score = max(0.0, min(1.0, round(score, 2)))
        self.logger.info(
            "Discovery candidate scored.",
            extra={
                "company_name": candidate.company_name,
                "confidence_score": score,
                "source_domain": source_domain,
            },
        )
        return score, reasons

    def find_existing_company_duplicate(
        self,
        *,
        normalized_name: str,
        website_domain: str | None,
    ) -> Company | None:
        """Find a trusted company duplicate by normalized name or website domain."""

        companies = list(self.session.execute(select(Company)).scalars().all())
        for company in companies:
            if self.normalize_name(company.vendor_name) == normalized_name:
                return company
            if website_domain and self.extract_domain(company.website) == website_domain:
                return company
        return None


class CompanyDiscoveryService:
    """Business workflow for discovery, review, approval, and rejection."""

    MIN_CONFIDENCE_TO_CREATE = 0.45

    def __init__(
        self,
        session: Session,
        *,
        repository: CompanyDiscoveryRepository | None = None,
        provider: CompanyDiscoveryProvider | None = None,
        company_service: CompanyService | None = None,
        verification_service: CompanyVerificationService | None = None,
        ingestion_service: CompanyIndexingService | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.session = session
        self.repository = repository or CompanyDiscoveryRepository(session)
        if provider is None:
            from app.discovery.tavily_provider import TavilyCompanyDiscoveryProvider
            self.provider = TavilyCompanyDiscoveryProvider()
        else:
            self.provider = provider
        self.company_service = company_service or CompanyService(session)
        self.verification_service = verification_service or CompanyVerificationService(session)
        self.ingestion_service = ingestion_service
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def discover_candidates(
        self,
        *,
        query: str | None = None,
        sector: str | None = None,
        country: str | None = None,
        limit: int = 10,
    ) -> DiscoveryRunSummary:
        """Discover, verify, dedupe, and persist pending candidates."""

        effective_limit = max(1, min(limit, 50))
        self.logger.info(
            "Starting company discovery.",
            extra={"query": query, "sector": sector, "country": country, "limit": effective_limit},
        )
        provider_candidates = self.provider.discover(
            query=query,
            sector=sector,
            country=country,
            limit=effective_limit,
        )
        summary = DiscoveryRunSummary(candidates_found=len(provider_candidates))
        provider_stats = getattr(self.provider, "last_stats", None)
        if isinstance(provider_stats, ProviderDiscoveryStats):
            summary.articles_fetched = provider_stats.articles_fetched
            summary.provider_candidates_extracted = provider_stats.candidates_extracted
            summary.provider_extraction_skipped = provider_stats.extraction_skipped
            summary.provider_extraction_details = list(provider_stats.extraction_details)
        else:
            summary.provider_candidates_extracted = len(provider_candidates)

        for provider_candidate in provider_candidates:
            normalized_name = self.verification_service.normalize_name(provider_candidate.company_name)
            website_domain = self.verification_service.extract_domain(provider_candidate.website)
            try:
                confidence_score, confidence_reasons = self.verification_service.validate_and_score(
                    provider_candidate
                )
            except DiscoveryValidationError as exc:
                summary.candidates_skipped += 1
                summary.skipped.append(
                    DiscoverySkippedCandidate(
                        company_name=provider_candidate.company_name,
                        evidence_url=provider_candidate.evidence_url,
                        reason=str(exc),
                    )
                )
                self.logger.info(
                    "Discovery candidate rejected during verification.",
                    extra={"company_name": provider_candidate.company_name, "reason": str(exc)},
                )
                continue

            existing_company = self.verification_service.find_existing_company_duplicate(
                normalized_name=normalized_name,
                website_domain=website_domain or None,
            )
            if existing_company is not None:
                summary.candidates_skipped += 1
                summary.skipped.append(
                    DiscoverySkippedCandidate(
                        company_name=provider_candidate.company_name,
                        evidence_url=provider_candidate.evidence_url,
                        reason="duplicate_existing_company",
                    )
                )
                self.logger.info(
                    "Discovery candidate duplicates trusted company.",
                    extra={"company_name": provider_candidate.company_name},
                )
                continue

            duplicate_pending = self.repository.find_pending_by_normalized_name(normalized_name)
            if duplicate_pending is None and website_domain:
                duplicate_pending = self.repository.find_pending_by_website_domain(website_domain)
            if duplicate_pending is not None:
                summary.candidates_skipped += 1
                summary.skipped.append(
                    DiscoverySkippedCandidate(
                        company_name=provider_candidate.company_name,
                        evidence_url=provider_candidate.evidence_url,
                        reason="duplicate_pending_candidate",
                    )
                )
                self.logger.info(
                    "Discovery candidate duplicates pending candidate.",
                    extra={"company_name": provider_candidate.company_name},
                )
                continue

            if confidence_score < self.MIN_CONFIDENCE_TO_CREATE:
                summary.candidates_skipped += 1
                summary.skipped.append(
                    DiscoverySkippedCandidate(
                        company_name=provider_candidate.company_name,
                        evidence_url=provider_candidate.evidence_url,
                        reason="confidence_below_pending_threshold",
                    )
                )
                continue

            candidate = CompanyDiscoveryCandidate(
                company_name=provider_candidate.company_name.strip(),
                normalized_name=normalized_name,
                website=provider_candidate.website,
                website_domain=website_domain or None,
                country=provider_candidate.country or country,
                description=provider_candidate.description,
                ai_category=provider_candidate.ai_category,
                provider=provider_candidate.provider,
                provider_company_id=provider_candidate.provider_company_id,
                provider_metadata=provider_candidate.provider_metadata,
                evidence_url=provider_candidate.evidence_url.strip(),
                evidence_title=provider_candidate.evidence_title,
                evidence_text=provider_candidate.evidence_text,
                source_domain=self.verification_service.extract_domain(provider_candidate.evidence_url),
                confidence_score=confidence_score,
                confidence_reasons=confidence_reasons,
                status=CompanyDiscoveryStatus.PENDING.value,
            )
            summary.items.append(self.repository.create(candidate))
            summary.candidates_created += 1

        self.logger.info(
            "Company discovery completed.",
            extra={
                "candidates_found": summary.candidates_found,
                "candidates_created": summary.candidates_created,
                "candidates_skipped": summary.candidates_skipped,
            },
        )
        return summary

    def list_pending(self, *, limit: int = 50) -> list[CompanyDiscoveryCandidate]:
        """Return pending candidates for human review."""

        return self.repository.list_pending(limit=limit)

    def get_candidate(self, candidate_id: UUID) -> CompanyDiscoveryCandidate | None:
        """Return one discovery candidate."""

        return self.repository.get_by_id(candidate_id)

    def approve_candidate(self, candidate_id: UUID) -> tuple[Company, str, int]:
        """Approve a pending candidate, create a trusted company, and index it."""

        candidate = self.repository.get_by_id(candidate_id)
        if candidate is None:
            raise LookupError(f"Discovery candidate '{candidate_id}' not found.")
        if candidate.status != CompanyDiscoveryStatus.PENDING.value:
            raise CandidateReviewStateError("candidate_already_reviewed")

        duplicate = self.verification_service.find_existing_company_duplicate(
            normalized_name=candidate.normalized_name,
            website_domain=candidate.website_domain,
        )
        if duplicate is not None:
            raise DuplicateCompanyError("duplicate_existing_company")

        deployment_evidence = "\n".join(
            value
            for value in (
                f"Discovery evidence: {candidate.evidence_title}" if candidate.evidence_title else None,
                f"Evidence URL: {candidate.evidence_url}",
                candidate.evidence_text,
            )
            if value
        )
        company = self.company_service.create_company(
            {
                "vendor_name": candidate.company_name,
                "country": candidate.country,
                "website": candidate.website,
                "company_type": "Discovered company",
                "ai_category": candidate.ai_category,
                "deployment_evidence": deployment_evidence,
            }
        )
        candidate.status = CompanyDiscoveryStatus.APPROVED.value
        candidate.reviewed_at = utc_now()
        candidate.approved_company_id = company.id
        self.repository.update(candidate)

        try:
            if self.ingestion_service is None:
                from app.ai.ingest import PostgresVectorIngestionService

                ingestion_service = PostgresVectorIngestionService(session=self.session)
            else:
                ingestion_service = self.ingestion_service
            indexed_chunks = ingestion_service.index_company_by_id(company.id)
        except (IndexingError, VectorStoreError):
            self.logger.exception(
                "Approved company was created but ChromaDB indexing failed.",
                extra={"company_id": str(company.id), "candidate_id": str(candidate.id)},
            )
            return company, "failed", 0

        self.logger.info(
            "Discovery candidate approved.",
            extra={
                "candidate_id": str(candidate.id),
                "company_id": str(company.id),
                "indexed_chunks": indexed_chunks,
            },
        )
        return company, "indexed", indexed_chunks

    def reject_candidate(
        self,
        candidate_id: UUID,
        *,
        rejection_reason: str | None = None,
    ) -> CompanyDiscoveryCandidate:
        """Reject a pending discovery candidate."""

        candidate = self.repository.get_by_id(candidate_id)
        if candidate is None:
            raise LookupError(f"Discovery candidate '{candidate_id}' not found.")
        if candidate.status != CompanyDiscoveryStatus.PENDING.value:
            raise CandidateReviewStateError("candidate_already_reviewed")

        candidate.status = CompanyDiscoveryStatus.REJECTED.value
        candidate.reviewed_at = utc_now()
        candidate.rejection_reason = rejection_reason
        updated = self.repository.update(candidate)
        self.logger.info(
            "Discovery candidate rejected.",
            extra={"candidate_id": str(candidate_id), "reason": rejection_reason or ""},
        )
        return updated


__all__ = [
    "CandidateReviewStateError",
    "CompanyDiscoveryProvider",
    "CompanyDiscoveryService",
    "CompanyVerificationService",
    "DiscoveryProviderAuthenticationError",
    "DiscoveryProviderCandidate",
    "DiscoveryProviderConfigurationError",
    "DiscoveryProviderRateLimitError",
    "DiscoveryProviderRequestError",
    "DiscoveryProviderResponseError",
    "DiscoveryRunSummary",
    "DiscoverySkippedCandidate",
    "DiscoveryValidationError",
    "DuplicateCompanyError",
    "NewsApiCompanyDiscoveryProvider",
    "ProviderExtractionDetail",
]
