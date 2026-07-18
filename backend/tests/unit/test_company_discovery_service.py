"""Unit tests for the company discovery workflow."""

from __future__ import annotations

import os
import logging
import unittest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ["DEBUG"] = "true"

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.models import Company, CompanyDiscoveryCandidate
from app.services.company_discovery_service import (
    CandidateReviewStateError,
    CompanyDiscoveryService,
    DiscoveryProviderCandidate,
    DiscoveryProviderConfigurationError,
    NewsApiCompanyDiscoveryProvider,
    ProviderDiscoveryStats,
    ProviderExtractionDetail,
)


class FakeProvider:
    """In-memory discovery provider for unit tests."""

    def __init__(
        self,
        candidates: list[DiscoveryProviderCandidate] | None = None,
        error: Exception | None = None,
        stats: ProviderDiscoveryStats | None = None,
    ):
        self.candidates = candidates or []
        self.error = error
        self.last_stats = stats

    def discover(self, *, query: str | None, sector: str | None, country: str | None, limit: int):
        if self.error is not None:
            raise self.error
        return self.candidates[:limit]


class FakeIngestionService:
    """Fake Chroma ingestion service that records company IDs."""

    def __init__(self) -> None:
        self.indexed_company_ids: list[object] = []

    def index_company_by_id(self, company_id):
        self.indexed_company_ids.append(company_id)
        return 1


class FakeNewsApiClient:
    """Fake NewsAPI client that returns prepared article dictionaries."""

    def __init__(self, articles: list[dict[str, object]]) -> None:
        self.articles = articles
        self.calls: list[dict[str, object]] = []

    def fetch_everything(self, query: str, *, from_date=None, page_size: int = 20, **kwargs):
        self.calls.append({"query": query, "from_date": from_date, "page_size": page_size, **kwargs})
        return self.articles


def valid_candidate(name: str = "Acme AI") -> DiscoveryProviderCandidate:
    """Build a valid provider candidate."""

    return DiscoveryProviderCandidate(
        company_name=name,
        evidence_url="https://techcrunch.com/acme-ai-launches-platform",
        evidence_title=f"{name} launches AI automation platform",
        evidence_text=f"{name} launched an artificial intelligence automation platform for enterprises.",
        description="Artificial intelligence automation platform for enterprise operations teams.",
        ai_category="AI automation",
    )


class NewsApiCompanyDiscoveryProviderTests(unittest.TestCase):
    """NewsAPI discovery provider unit tests."""

    def build_provider(self, articles: list[dict[str, object]]) -> NewsApiCompanyDiscoveryProvider:
        return NewsApiCompanyDiscoveryProvider(client=FakeNewsApiClient(articles))

    def test_build_query_uses_broad_context_without_country_filter(self) -> None:
        query = NewsApiCompanyDiscoveryProvider._build_query(
            query="AI computer vision food manufacturing",
            sector="Food Manufacturing",
            country="Germany",
        )

        self.assertIn('"computer vision"', query)
        self.assertIn('"food manufacturing"', query)
        self.assertIn("AI", query)
        self.assertNotIn("Germany", query)
        self.assertNotIn("AI computer vision food manufacturing Food Manufacturing Germany", query)
        self.assertNotIn("AND (AI OR", query)
        self.assertIn("startup OR company OR vendor OR technology OR platform OR software", query)
        self.assertIn("NOT (watch OR video OR live OR updates)", query)

    def test_extracts_existing_launches_headline(self) -> None:
        name = NewsApiCompanyDiscoveryProvider._extract_company_name(
            "Acme AI launches computer vision platform for food inspection"
        )

        self.assertEqual(name, "Acme AI")

    def test_extracts_existing_raises_headline(self) -> None:
        name = NewsApiCompanyDiscoveryProvider._extract_company_name(
            "Acme AI raises $20M for manufacturing automation"
        )

        self.assertEqual(name, "Acme AI")

    def test_extracts_alternative_from_headline(self) -> None:
        name = NewsApiCompanyDiscoveryProvider._extract_company_name(
            "New AI platform from Acme improves quality inspection"
        )

        self.assertEqual(name, "Acme")

    def test_generic_headline_returns_no_company(self) -> None:
        name = NewsApiCompanyDiscoveryProvider._extract_company_name(
            "AI market report forecasts food manufacturing growth"
        )

        self.assertIsNone(name)

    def test_watch_is_rejected_as_company(self) -> None:
        name = NewsApiCompanyDiscoveryProvider._extract_company_name(
            "WATCH: New AI system improves food manufacturing"
        )

        self.assertIsNone(name)

    def test_show_hn_is_rejected_as_company(self) -> None:
        name = NewsApiCompanyDiscoveryProvider._extract_company_name(
            "Show HN: Computer vision platform for food manufacturing"
        )

        self.assertIsNone(name)

    def test_allowed_uppercase_company_names_remain_valid(self) -> None:
        for company_name in ("IBM", "SAP", "ABB", "NVIDIA"):
            with self.subTest(company_name=company_name):
                name = NewsApiCompanyDiscoveryProvider._extract_company_name(
                    f"{company_name} launches AI platform for manufacturers"
                )

                self.assertEqual(name, company_name)

    def test_valid_company_from_realistic_ai_headline_is_extracted(self) -> None:
        name = NewsApiCompanyDiscoveryProvider._extract_company_name(
            "German food manufacturer adopts Acme AI technology"
        )

        self.assertEqual(name, "Acme AI")

    def test_description_assisted_extraction_works(self) -> None:
        name = NewsApiCompanyDiscoveryProvider._extract_company_name(
            "Food manufacturers turn to computer vision for quality checks",
            "Startup called Acme Vision develops AI software for production-line inspection.",
        )

        self.assertEqual(name, "Acme Vision")

    def test_explicit_ai_startup_phrase_extracts_company(self) -> None:
        name = NewsApiCompanyDiscoveryProvider._extract_company_name(
            "AI bottleneck debates heat up",
            "AI startup Subquadratic came out of stealth with software for faster inference.",
        )

        self.assertEqual(name, "Subquadratic")

    def test_explicit_company_type_extraction_takes_priority_over_newsletter_title(self) -> None:
        name = NewsApiCompanyDiscoveryProvider._extract_company_name(
            "The Download: AI bottleneck debates, and BCI trials take off",
            "AI startup Subquadratic came out of stealth with software for faster inference.",
        )

        self.assertEqual(name, "Subquadratic")

    def test_the_download_is_not_returned_as_company(self) -> None:
        name = NewsApiCompanyDiscoveryProvider._extract_company_name(
            "The Download: AI bottleneck debates, and BCI trials take off"
        )

        self.assertIsNone(name)

    def test_unrelated_abc_news_video_headline_does_not_become_candidate(self) -> None:
        provider = self.build_provider(
            [
                {
                    "title": "ABC News: WATCH live updates on unrelated politics",
                    "url": "https://abcnews.go.com/video/example",
                    "description": "Video coverage and live updates from ABC News.",
                }
            ]
        )

        candidates = provider.discover(query="AI computer vision food manufacturing", sector=None, country=None, limit=10)

        self.assertEqual(candidates, [])
        self.assertEqual(provider.last_stats.unrelated_article, 1)
        self.assertEqual(provider.last_stats.extraction_details[0].source_domain, "abcnews.go.com")
        self.assertEqual(provider.last_stats.extraction_details[0].extraction_skip_reason, "unrelated_article")

    def test_latest_editorial_headlines_are_blocked_as_generic_names(self) -> None:
        for title in (
            "Latest launches AI platform for manufacturers",
            "Latest News launches AI platform for manufacturers",
            "The Latest launches AI platform for manufacturers",
        ):
            with self.subTest(title=title):
                name = NewsApiCompanyDiscoveryProvider._extract_company_name(title)

                self.assertIsNone(name)

    def test_provider_records_safe_extraction_details_for_skipped_articles(self) -> None:
        long_title = "Market report " + ("very " * 60) + "forecasts AI growth"
        article = {
            "title": long_title,
            "url": "https://example.com/report",
            "description": "Artificial intelligence market report forecasts growth.",
            "content": "This full content should never appear in extraction diagnostics.",
        }
        provider = self.build_provider([article])

        candidates = provider.discover(query="AI inspection", sector=None, country=None, limit=10)

        self.assertEqual(candidates, [])
        self.assertEqual(provider.last_stats.no_company_name_extracted, 1)
        self.assertEqual(provider.last_stats.extraction_skipped, 1)
        self.assertEqual(len(provider.last_stats.extraction_details), 1)
        detail = provider.last_stats.extraction_details[0]
        self.assertEqual(detail.source_domain, "example.com")
        self.assertEqual(detail.extraction_skip_reason, "no_company_name_extracted")
        self.assertLessEqual(len(detail.title or ""), NewsApiCompanyDiscoveryProvider.DIAGNOSTIC_TITLE_MAX_LENGTH)
        self.assertNotIn("full content", detail.title or "")

    def test_provider_tracks_articles_with_missing_url(self) -> None:
        provider = self.build_provider(
            [
                {
                    "title": "Acme AI launches computer vision platform",
                    "url": "",
                    "description": "Acme AI launched artificial intelligence software.",
                },
                {
                    "title": "Beta Vision launches AI inspection platform",
                    "url": "https://example.com/beta-vision",
                    "description": "Beta Vision launched artificial intelligence inspection software.",
                },
            ]
        )

        candidates = provider.discover(query="AI inspection", sector=None, country=None, limit=10)

        self.assertEqual(len(candidates), 1)
        self.assertEqual(provider.last_stats.articles_fetched, 2)
        self.assertEqual(provider.last_stats.skipped_missing_url, 1)
        self.assertEqual(provider.last_stats.candidates_extracted, 1)
        self.assertEqual(provider.last_stats.missing_url, 1)
        self.assertEqual(provider.last_stats.extraction_details[0].extraction_skip_reason, "missing_url")

    def test_provider_deduplicates_repeated_candidates(self) -> None:
        article = {
            "title": "Acme AI launches computer vision platform",
            "url": "https://example.com/acme-ai",
            "description": "Acme AI launched artificial intelligence software.",
        }
        provider = self.build_provider([article, dict(article)])

        candidates = provider.discover(query="AI inspection", sector=None, country=None, limit=10)

        self.assertEqual(len(candidates), 1)
        self.assertEqual(provider.last_stats.skipped_duplicates, 1)
        self.assertEqual(provider.last_stats.provider_duplicate, 1)
        self.assertEqual(provider.last_stats.extraction_details[0].extraction_skip_reason, "provider_duplicate")

    def test_provider_logs_structured_extraction_failure_fields(self) -> None:
        logger_name = "tests.discovery_provider"
        provider = NewsApiCompanyDiscoveryProvider(
            client=FakeNewsApiClient(
                [
                    {
                        "title": "AI market report forecasts growth",
                        "url": "https://example.com/report",
                        "description": "Artificial intelligence market report.",
                    }
                ]
            ),
            logger=logging.getLogger(logger_name),
        )

        with self.assertLogs(logger_name, level="INFO") as logs:
            provider.discover(query="AI inspection", sector=None, country=None, limit=10)

        skip_record = next(
            record
            for record in logs.records
            if record.getMessage() == "NewsAPI discovery article skipped during extraction."
        )
        self.assertEqual(skip_record.article_title, "AI market report forecasts growth")
        self.assertEqual(skip_record.source_domain, "example.com")
        self.assertEqual(skip_record.extraction_rule_attempted, "title_then_description_patterns")
        self.assertEqual(skip_record.extraction_skip_reason, "no_company_name_extracted")

    def test_provider_returns_candidates_for_valid_articles(self) -> None:
        provider = self.build_provider(
            [
                {
                    "title": "Acme AI launches computer vision platform",
                    "url": "https://example.com/acme-ai",
                    "description": "Acme AI launched artificial intelligence inspection software.",
                    "content": "The platform helps manufacturers automate quality inspection.",
                }
            ]
        )

        candidates = provider.discover(
            query="AI computer vision food manufacturing",
            sector="Food Manufacturing",
            country="Germany",
            limit=10,
        )

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].company_name, "Acme AI")
        self.assertEqual(candidates[0].evidence_url, "https://example.com/acme-ai")
        self.assertEqual(provider.last_stats.candidates_extracted, 1)
        self.assertEqual(provider.client.calls[0]["sort_by"], "relevancy")
        self.assertEqual(provider.client.calls[0]["search_in"], "title,description,content")
        self.assertEqual(provider.client.calls[0]["exclude_domains"], ["abcnews.go.com"])


class CompanyDiscoveryServiceTests(unittest.TestCase):
    """Company discovery workflow unit tests."""

    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite://",
            future=True,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        testing_session = sessionmaker(bind=self.engine, class_=Session, future=True)
        self.session = testing_session()

    def tearDown(self) -> None:
        self.session.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def build_service(
        self,
        candidates: list[DiscoveryProviderCandidate],
        ingestion_service: FakeIngestionService | None = None,
        provider_stats: ProviderDiscoveryStats | None = None,
    ) -> CompanyDiscoveryService:
        return CompanyDiscoveryService(
            session=self.session,
            provider=FakeProvider(candidates, stats=provider_stats),
            ingestion_service=ingestion_service,
        )

    def test_valid_candidate_becomes_pending(self) -> None:
        service = self.build_service([valid_candidate()])

        summary = service.discover_candidates(query="AI automation")

        self.assertEqual(summary.candidates_found, 1)
        self.assertEqual(summary.candidates_created, 1)
        self.assertEqual(summary.items[0].status, "pending")
        self.assertGreaterEqual(summary.items[0].confidence_score, 0.45)

    def test_provider_extraction_details_are_copied_to_summary(self) -> None:
        stats = ProviderDiscoveryStats(
            articles_fetched=1,
            no_company_name_extracted=1,
            extraction_details=[
                ProviderExtractionDetail(
                    title="AI market report forecasts growth",
                    source_domain="example.com",
                    extraction_skip_reason="no_company_name_extracted",
                )
            ],
        )
        service = self.build_service([], provider_stats=stats)

        summary = service.discover_candidates(query="AI automation")

        self.assertEqual(summary.articles_fetched, 1)
        self.assertEqual(summary.provider_extraction_skipped, 1)
        self.assertEqual(summary.provider_extraction_details[0].source_domain, "example.com")
        self.assertEqual(
            summary.provider_extraction_details[0].extraction_skip_reason,
            "no_company_name_extracted",
        )

    def test_candidate_matching_existing_company_is_skipped(self) -> None:
        self.session.add(Company(vendor_name="Microsoft Corporation"))
        self.session.commit()
        service = self.build_service([valid_candidate("Microsoft")])

        summary = service.discover_candidates(query="AI")

        self.assertEqual(summary.candidates_created, 0)
        self.assertEqual(summary.skipped[0].reason, "duplicate_existing_company")

    def test_duplicate_pending_candidate_is_skipped(self) -> None:
        service = self.build_service([valid_candidate()])
        self.assertEqual(service.discover_candidates(query="AI").candidates_created, 1)

        summary = service.discover_candidates(query="AI")

        self.assertEqual(summary.candidates_created, 0)
        self.assertEqual(summary.skipped[0].reason, "duplicate_pending_candidate")

    def test_candidate_without_evidence_is_rejected(self) -> None:
        service = self.build_service(
            [
                DiscoveryProviderCandidate(
                    company_name="No Evidence AI",
                    evidence_url="",
                    evidence_title="No Evidence AI launches AI platform",
                    evidence_text="No Evidence AI launches artificial intelligence software.",
                )
            ],
        )

        summary = service.discover_candidates(query="AI")

        self.assertEqual(summary.candidates_created, 0)
        self.assertEqual(summary.skipped[0].reason, "invalid_or_missing_evidence_url")

    def test_low_quality_package_release_content_is_rejected(self) -> None:
        candidate = valid_candidate("Package AI")
        candidate.evidence_url = "https://github.com/package-ai/releases/tag/v1.2.3"
        candidate.evidence_title = "Package AI release notes v1.2.3"
        service = self.build_service([candidate])

        summary = service.discover_candidates(query="AI")

        self.assertEqual(summary.candidates_created, 0)
        self.assertEqual(summary.skipped[0].reason, "low_quality_or_package_release_content")

    def test_pending_candidate_can_be_approved_and_indexed(self) -> None:
        ingestion = FakeIngestionService()
        service = self.build_service([valid_candidate()], ingestion_service=ingestion)
        candidate = service.discover_candidates(query="AI").items[0]

        company, indexing_status, indexed_chunks = service.approve_candidate(candidate.id)

        self.assertEqual(company.vendor_name, "Acme AI")
        self.assertEqual(indexing_status, "indexed")
        self.assertEqual(indexed_chunks, 1)
        self.assertEqual(ingestion.indexed_company_ids, [company.id])

    def test_approved_candidate_becomes_real_company(self) -> None:
        service = self.build_service([valid_candidate()], ingestion_service=FakeIngestionService())
        candidate = service.discover_candidates(query="AI").items[0]

        company, _, _ = service.approve_candidate(candidate.id)

        persisted = self.session.execute(select(Company).where(Company.id == company.id)).scalars().first()
        self.assertIsNotNone(persisted)
        self.assertEqual(persisted.vendor_name, "Acme AI")

    def test_rejected_candidate_is_not_inserted_into_companies(self) -> None:
        service = self.build_service([valid_candidate()])
        candidate = service.discover_candidates(query="AI").items[0]

        rejected = service.reject_candidate(candidate.id, rejection_reason="not relevant")

        self.assertEqual(rejected.status, "rejected")
        self.assertEqual(self.session.execute(select(Company)).scalars().all(), [])

    def test_already_reviewed_candidate_cannot_be_reviewed_again(self) -> None:
        service = self.build_service([valid_candidate()], ingestion_service=FakeIngestionService())
        candidate = service.discover_candidates(query="AI").items[0]
        service.approve_candidate(candidate.id)

        with self.assertRaises(CandidateReviewStateError):
            service.reject_candidate(candidate.id)

    def test_provider_errors_are_safely_raised(self) -> None:
        service = CompanyDiscoveryService(
            session=self.session,
            provider=FakeProvider(error=DiscoveryProviderConfigurationError("NEWS_API_KEY is not configured.")),
        )

        with self.assertRaises(DiscoveryProviderConfigurationError):
            service.discover_candidates(query="AI")

    def test_rejected_candidate_is_not_indexed(self) -> None:
        ingestion = FakeIngestionService()
        service = self.build_service([valid_candidate()], ingestion_service=ingestion)
        candidate = service.discover_candidates(query="AI").items[0]

        service.reject_candidate(candidate.id)

        self.assertEqual(ingestion.indexed_company_ids, [])
        stored = self.session.execute(select(CompanyDiscoveryCandidate)).scalars().first()
        self.assertEqual(stored.status, "rejected")


if __name__ == "__main__":
    unittest.main()
