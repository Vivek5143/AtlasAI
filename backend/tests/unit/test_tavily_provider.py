"""Unit tests for Tavily Search API client and Tavily + Gemini Company Discovery Provider.

ALL TESTS IN THIS FILE USE FAKE/MOCKED CLIENTS AND FAKE LLMs.
0 REAL EXTERNAL API CALLS (0 Tavily credits, 0 Gemini credits, 0 NewsAPI credits).
"""

from __future__ import annotations

import json
import os
import unittest
import unittest.mock
from typing import Any

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ["DEBUG"] = "true"
os.environ["GOOGLE_API_KEY"] = ""
os.environ["GEMINI_API_KEY"] = ""
os.environ["TAVILY_API_KEY"] = ""
os.environ["NEWS_API_KEY"] = ""

from app.clients.tavily_client import (
    TavilyAuthenticationError,
    TavilyClient,
    TavilyConfigurationError,
    TavilyRateLimitError,
)
from app.discovery.tavily_provider import TavilyCompanyDiscoveryProvider
from app.services.company_discovery_service import (
    DiscoveryProviderAuthenticationError,
    DiscoveryProviderConfigurationError,
    DiscoveryProviderRateLimitError,
)


class FakeTavilyClient:
    """Fake Tavily client returning prepared web-search results. 0 real external API calls."""

    def __init__(
        self,
        results: list[dict[str, object]] | None = None,
        search_responses: dict[str, list[dict[str, object]]] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.results = results or []
        self.search_responses = search_responses or {}
        self.error = error
        self.calls: list[dict[str, object]] = []

    def search_companies(
        self,
        *,
        query: str | None = None,
        sector: str | None = None,
        country: str | None = None,
        max_results: int = 10,
        search_depth: str = "basic",
    ) -> list[dict[str, object]]:
        self.calls.append(
            {
                "query": query,
                "sector": sector,
                "country": country,
                "max_results": max_results,
                "search_depth": search_depth,
            }
        )

        if self.error:
            raise self.error

        if query:
            if query in self.search_responses:
                return self.search_responses[query]
            for key, response in self.search_responses.items():
                lowered_query = query.lower()
                lowered_key = key.lower()
                if lowered_key in lowered_query or lowered_query in lowered_key:
                    return response

        return self.results


class FakeLLMExtractor:
    """Fake callable LLM returning deterministic structured extraction output."""

    def __init__(
        self,
        response_data: list[dict[str, Any]] | dict[str, Any] | str | None = None,
        should_fail: bool = False,
    ) -> None:
        self.response_data = response_data if response_data is not None else []
        self.should_fail = should_fail
        self.invocations: list[Any] = []

    def __call__(
        self,
        items: list[dict[str, str]],
    ) -> list[dict[str, Any]] | dict[str, Any] | str:
        self.invocations.append(items)
        if self.should_fail:
            raise RuntimeError("Gemini API call failed simulated")
        return self.response_data


class FakeLangChainLLM:
    """Fake LangChain-compatible LLM with configurable response.content shape."""

    def __init__(self, content: Any) -> None:
        self.content = content
        self.prompts: list[str] = []

    def invoke(self, prompt: str) -> Any:
        self.prompts.append(prompt)

        class FakeResponse:
            pass

        response = FakeResponse()
        response.content = self.content
        return response


class TavilyClientQueryTests(unittest.TestCase):
    """Tests for Tavily company-search query construction."""

    def test_build_company_query_appends_companies_keyword(self) -> None:
        client = TavilyClient(api_key="test-tavily-key")
        built = client._build_company_query(
            query="AI food technology",
            sector="Food Technology",
            country="Germany",
        )
        self.assertIn("ai food technology", built.lower())
        self.assertIn("food technology", built.lower())
        self.assertIn("germany", built.lower())
        self.assertTrue(built.endswith("companies"))

    def test_build_company_query_preserves_existing_startup_keyword(self) -> None:
        client = TavilyClient(api_key="test-tavily-key")
        built = client._build_company_query(query="best AI startups in Germany")
        self.assertNotIn(" companies", built)
        self.assertEqual(built, "best AI startups in Germany")

    def test_build_company_query_preserves_sector_and_country_when_not_in_query(self) -> None:
        client = TavilyClient(api_key="test-tavily-key")
        built = client._build_company_query(
            query="AI companies",
            sector="Food Technology",
            country="Germany",
        )
        self.assertIn("AI companies", built)
        self.assertIn("Food Technology", built)
        self.assertIn("Germany", built)

    def test_build_company_query_does_not_duplicate_sector_and_country(self) -> None:
        client = TavilyClient(api_key="test-tavily-key")
        built = client._build_company_query(
            query="AI food technology startups Germany",
            sector="Food Technology",
            country="Germany",
        )
        self.assertEqual(
            built,
            "AI food technology startups Germany",
        )

    def test_search_companies_passes_built_query_to_http_layer(self) -> None:
        """Verify search_companies uses _build_company_query before any HTTP call."""
        client = TavilyClient(api_key="test-tavily-key")
        expected = client._build_company_query(
            query="Foodforecast",
            sector="Food Technology",
            country="Germany",
        )

        with unittest.mock.patch.object(client, "_raise_for_error_status"), unittest.mock.patch(
            "app.clients.tavily_client.requests.post",
            return_value=unittest.mock.Mock(status_code=200, text='{"results": []}'),
        ) as mock_post:
            client.search_companies(
                query="Foodforecast",
                sector="Food Technology",
                country="Germany",
                max_results=5,
            )

        payload = json.loads(mock_post.call_args.kwargs["data"])
        self.assertEqual(payload["query"], expected)


class TavilyClientTests(unittest.TestCase):
    """TavilyClient unit tests using local inputs only."""

    def test_normalize_result_curates_provider_metadata(self) -> None:
        client = TavilyClient(api_key="test-tavily-key")

        raw_result = {
            "title": "Acme AI | Enterprise AI Automation",
            "url": "https://acmeai.com",
            "content": "Acme AI provides enterprise AI automation solutions.",
            "score": 0.94,
            "raw_content": "x" * 5000,
            "unwanted_huge_field": "y" * 5000,
        }

        normalized = client._normalize_result(raw_result)

        self.assertEqual(normalized["title"], "Acme AI | Enterprise AI Automation")
        self.assertEqual(normalized["url"], "https://acmeai.com")
        self.assertEqual(
            normalized["content"],
            "Acme AI provides enterprise AI automation solutions.",
        )
        self.assertEqual(normalized["score"], 0.94)

        metadata = normalized["provider_metadata"]
        self.assertEqual(metadata["source_url"], "https://acmeai.com")
        self.assertEqual(metadata["search_score"], 0.94)
        self.assertNotIn("raw_content", metadata)
        self.assertNotIn("unwanted_huge_field", metadata)

    def test_missing_api_key_raises_configuration_error(self) -> None:
        client = TavilyClient(api_key="")
        with self.assertRaises(TavilyConfigurationError):
            client.search_companies(query="AI companies", sector=None, country=None)


class TavilyProviderGeminiParsingTests(unittest.TestCase):
    """Direct tests for Gemini parsing helpers on TavilyCompanyDiscoveryProvider."""

    def setUp(self) -> None:
        self.provider = TavilyCompanyDiscoveryProvider(
            client=FakeTavilyClient(),
            llm=FakeLLMExtractor([]),
            perform_website_lookup=False,
        )

    def test_coerce_llm_content_extracts_text_from_content_blocks(self) -> None:
        content = [
            {
                "type": "text",
                "text": '{"is_company_mention": true, "company_name": "Foodforecast"}',
                "extras": {"signature": "fake-signature"},
            }
        ]
        text = self.provider._coerce_llm_content(content)
        self.assertIn("Foodforecast", text)
        self.assertNotIn("fake-signature", text)

    def test_coerce_llm_content_returns_plain_string(self) -> None:
        self.assertEqual(
            self.provider._coerce_llm_content('{"company_name": "Acme"}'),
            '{"company_name": "Acme"}',
        )

    def test_parse_json_payload_handles_markdown_fenced_json(self) -> None:
        raw = """```json
{"is_company_mention": true, "company_name": "Foodforecast", "confidence": 0.95}
```"""
        parsed = self.provider._parse_json_payload(raw)
        self.assertIsInstance(parsed, dict)
        self.assertEqual(parsed["company_name"], "Foodforecast")

    def test_is_company_mention_false_produces_no_company(self) -> None:
        record = self.provider._normalize_extraction_record(
            {
                "is_company_mention": False,
                "company_name": "Foodforecast",
                "confidence": 0.99,
            }
        )
        self.assertIsNone(record)

    def test_low_confidence_produces_no_company(self) -> None:
        record = self.provider._normalize_extraction_record(
            {
                "is_company_mention": True,
                "company_name": "Foodforecast",
                "confidence": 0.2,
            }
        )
        self.assertIsNone(record)

    def test_malformed_json_extraction_fails_closed(self) -> None:
        llm = FakeLangChainLLM(content="NOT VALID JSON OUTPUT")
        provider = TavilyCompanyDiscoveryProvider(client=FakeTavilyClient(), llm=llm)

        records, method = provider._extract_companies_with_gemini(
            [
                {
                    "title": "Article title",
                    "url": "https://example.com/article",
                    "content": "Some content.",
                }
            ]
        )

        self.assertEqual(records, [])
        self.assertEqual(method, "failed")

    def test_gemini_content_block_response_is_parsed(self) -> None:
        """Regression for langchain-google-genai 4.2.7 list-shaped response.content."""
        llm = FakeLangChainLLM(
            content=[
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "is_company_mention": True,
                            "company_name": "Foodforecast",
                            "description": "AI-powered food forecasting company.",
                            "matches_query": True,
                            "matches_sector": True,
                            "matches_country": True,
                            "confidence": 0.95,
                        }
                    ),
                    "extras": {"signature": "fake-signature"},
                }
            ]
        )
        provider = TavilyCompanyDiscoveryProvider(client=FakeTavilyClient(), llm=llm)

        records, method = provider._extract_companies_with_gemini(
            [
                {
                    "title": (
                        "German AI FoodTech startup Foodforecast raises €8 million"
                    ),
                    "url": "https://example-news.com/foodforecast",
                    "content": (
                        "Foodforecast has raised €8 million for its AI food "
                        "forecasting platform."
                    ),
                }
            ]
        )

        self.assertEqual(method, "gemini_structured")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["company_name"], "Foodforecast")

    def test_gemini_markdown_fenced_json_via_langchain_llm(self) -> None:
        fenced = (
            "```json\n"
            '{"is_company_mention": true, "company_name": "Foodforecast", "confidence": 0.95}\n'
            "```"
        )
        provider = TavilyCompanyDiscoveryProvider(
            client=FakeTavilyClient(),
            llm=FakeLangChainLLM(content=fenced),
        )

        records, method = provider._extract_companies_with_gemini(
            [
                {
                    "title": "Foodforecast funding news",
                    "url": "https://example.com/article",
                    "content": "Foodforecast raised funding.",
                }
            ]
        )

        self.assertEqual(method, "gemini_structured")
        self.assertEqual(records[0]["company_name"], "Foodforecast")


class TavilyCompanyDiscoveryProviderRegressionTests(unittest.TestCase):
    """Regression tests for known live-failure cases (Cases A–J)."""

    def test_case_a_reject_headline_sentence_as_company_name(self) -> None:
        article_title = (
            "German food tech company secures €8 million to combat food waste"
        )
        fake_client = FakeTavilyClient(
            results=[
                {
                    "title": article_title,
                    "url": "https://yumda.com/news/german-food-tech-secures-8m",
                    "content": article_title,
                    "score": 0.90,
                }
            ]
        )
        fake_llm = FakeLLMExtractor(
            {
                "is_company_mention": True,
                "company_name": article_title,
                "confidence": 0.99,
            }
        )
        provider = TavilyCompanyDiscoveryProvider(
            client=fake_client,
            llm=fake_llm,
            perform_website_lookup=False,
        )

        candidates = provider.discover(query="AI food", sector=None, country=None, limit=5)

        self.assertEqual(candidates, [])
        self.assertGreater(provider.last_stats.blocked_generic_name, 0)

    def test_case_b_reject_generic_article_title(self) -> None:
        fake_client = FakeTavilyClient(
            results=[
                {
                    "title": (
                        "Mastering Food Technologies: A Guide to Germany's "
                        "Culinary Innovation"
                    ),
                    "url": "https://duscons.com/article/mastering-food-technologies",
                    "content": "A guide to culinary innovation in Germany.",
                    "score": 0.85,
                }
            ]
        )
        provider = TavilyCompanyDiscoveryProvider(
            client=fake_client,
            llm=FakeLLMExtractor([]),
            perform_website_lookup=False,
        )

        candidates = provider.discover(query="Food Tech", sector=None, country=None, limit=5)

        self.assertEqual(candidates, [])
        self.assertGreater(provider.last_stats.unrelated_article, 0)

    def test_case_c_reject_publication_title_greentech_on_a_plate(self) -> None:
        fake_client = FakeTavilyClient(
            results=[
                {
                    "title": "GreenTech on a Plate",
                    "url": "https://gtai.de/publication/greentech-on-a-plate",
                    "content": "A publication overview of green technology in agriculture.",
                    "score": 0.88,
                }
            ]
        )
        fake_llm = FakeLLMExtractor(
            {
                "is_company_mention": True,
                "company_name": "GreenTech on a Plate",
                "confidence": 0.99,
            }
        )
        provider = TavilyCompanyDiscoveryProvider(
            client=fake_client,
            llm=fake_llm,
            perform_website_lookup=False,
        )

        candidates = provider.discover(query="GreenTech", sector=None, country=None, limit=5)

        self.assertEqual(candidates, [])
        self.assertGreater(provider.last_stats.unrelated_article, 0)

    def test_case_d_reject_listicle_best_ai_startups(self) -> None:
        fake_client = FakeTavilyClient(
            results=[
                {
                    "title": "Best AI Startups in Germany (2026)",
                    "url": "https://seedtable.com/best-ai-startups-in-germany",
                    "content": "A list of the best AI startups in Germany.",
                    "score": 0.92,
                }
            ]
        )
        provider = TavilyCompanyDiscoveryProvider(
            client=fake_client,
            llm=FakeLLMExtractor([]),
            perform_website_lookup=False,
        )

        candidates = provider.discover(
            query="AI startups",
            sector=None,
            country=None,
            limit=5,
        )

        self.assertEqual(candidates, [])
        self.assertGreater(provider.last_stats.unrelated_article, 0)

    def test_case_e_reject_academic_journal_as_official_website(self) -> None:
        fake_client = FakeTavilyClient(
            search_responses={
                "AI trends": [
                    {
                        "title": "The Latest AI Trends Transforming The Food Industry",
                        "url": "https://forbes.com/sites/food-ai-trends",
                        "content": "Trends in AI food industry.",
                        "score": 0.89,
                    }
                ],
                "official website": [
                    {
                        "title": "Academic PMC Paper",
                        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC11488428",
                        "content": "Academic research article.",
                        "score": 0.95,
                    }
                ],
            }
        )
        fake_llm = FakeLLMExtractor(
            {
                "is_company_mention": True,
                "company_name": "The Latest AI Trends",
                "confidence": 0.99,
            }
        )
        provider = TavilyCompanyDiscoveryProvider(
            client=fake_client,
            llm=fake_llm,
            perform_website_lookup=True,
        )

        candidates = provider.discover(query="AI trends", sector=None, country=None, limit=5)

        self.assertEqual(candidates, [])

    def test_case_f_valid_scenario_foodforecast(self) -> None:
        fake_client = FakeTavilyClient(
            search_responses={
                "Foodforecast": [
                    {
                        "title": (
                            "German AI FoodTech startup Foodforecast raises €8 million "
                            "to tackle ultra-fresh food wastage"
                        ),
                        "url": "https://eu-startups.com/2026/01/foodforecast-raises-8m",
                        "content": (
                            "German AI FoodTech startup Foodforecast raises €8 million "
                            "to tackle ultra-fresh food wastage."
                        ),
                        "score": 0.95,
                    }
                ],
                "Foodforecast official website": [
                    {
                        "title": "Foodforecast | Official Website",
                        "url": "https://foodforecast.com",
                        "content": "Foodforecast AI demand forecasting software.",
                        "score": 0.98,
                    }
                ],
            }
        )
        fake_llm = FakeLLMExtractor(
            {
                "is_company_mention": True,
                "company_name": "Foodforecast",
                "description": "AI demand forecasting software for fresh food.",
                "confidence": 0.95,
            }
        )
        provider = TavilyCompanyDiscoveryProvider(
            client=fake_client,
            llm=fake_llm,
            perform_website_lookup=True,
        )

        candidates = provider.discover(
            query="Foodforecast",
            sector="Food Technology",
            country="Germany",
            limit=5,
        )

        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate.company_name, "Foodforecast")
        self.assertEqual(candidate.website, "https://foodforecast.com")
        self.assertEqual(
            candidate.evidence_url,
            "https://eu-startups.com/2026/01/foodforecast-raises-8m",
        )
        self.assertEqual(candidate.provider, "tavily")
        self.assertEqual(
            candidate.provider_metadata["extraction_method"],
            "gemini_structured",
        )

    def test_case_g_gemini_failure_skips_without_title_fallback(self) -> None:
        article_title = "Some Unknown Web Page Title"
        fake_client = FakeTavilyClient(
            results=[
                {
                    "title": article_title,
                    "url": "https://example.com/page",
                    "content": "Content snippet.",
                    "score": 0.80,
                }
            ]
        )
        provider = TavilyCompanyDiscoveryProvider(
            client=fake_client,
            llm=FakeLLMExtractor(should_fail=True),
            perform_website_lookup=False,
        )

        candidates = provider.discover(query="AI", sector=None, country=None, limit=5)

        self.assertEqual(candidates, [])
        self.assertGreater(provider.last_stats.no_company_name_extracted, 0)

    def test_case_h_gemini_malformed_json_skips_without_title_fallback(self) -> None:
        fake_client = FakeTavilyClient(
            results=[
                {
                    "title": "Another Web Page Title",
                    "url": "https://example.com/page2",
                    "content": "Content snippet.",
                    "score": 0.80,
                }
            ]
        )
        provider = TavilyCompanyDiscoveryProvider(
            client=fake_client,
            llm=FakeLLMExtractor(response_data="NOT VALID JSON OUTPUT"),
            perform_website_lookup=False,
        )

        candidates = provider.discover(query="AI", sector=None, country=None, limit=5)

        self.assertEqual(candidates, [])

    def test_case_i_no_verified_official_website_skips_candidate(self) -> None:
        fake_client = FakeTavilyClient(
            search_responses={
                "AcmeAI": [
                    {
                        "title": "Article mentioning AcmeAI technology",
                        "url": "https://news-aggregator.com/article/acmeai",
                        "content": "AcmeAI is an enterprise startup.",
                        "score": 0.90,
                    }
                ],
                "AcmeAI official website": [],
            }
        )
        fake_llm = FakeLLMExtractor(
            {
                "is_company_mention": True,
                "company_name": "AcmeAI",
                "confidence": 0.95,
            }
        )
        provider = TavilyCompanyDiscoveryProvider(
            client=fake_client,
            llm=fake_llm,
            perform_website_lookup=True,
        )

        candidates = provider.discover(query="AcmeAI", sector=None, country=None, limit=5)

        self.assertEqual(candidates, [])
        self.assertGreater(provider.last_stats.missing_url, 0)

    def test_case_j_company_domain_mismatch_rejects_candidate(self) -> None:
        fake_client = FakeTavilyClient(
            search_responses={
                "Foodforecast": [
                    {
                        "title": "Article mentioning Foodforecast",
                        "url": "https://industry-news.com/article/foodforecast",
                        "content": "Foodforecast AI demand forecasting software.",
                        "score": 0.90,
                    }
                ],
                "Foodforecast official website": [
                    {
                        "title": "Unrelated Tech Company",
                        "url": "https://unrelatedtechnologycompany.com",
                        "content": "Unrelated technology company.",
                        "score": 0.95,
                    }
                ],
            }
        )
        fake_llm = FakeLLMExtractor(
            {
                "is_company_mention": True,
                "company_name": "Foodforecast",
                "confidence": 0.95,
            }
        )
        provider = TavilyCompanyDiscoveryProvider(
            client=fake_client,
            llm=fake_llm,
            perform_website_lookup=True,
        )

        candidates = provider.discover(
            query="Foodforecast",
            sector=None,
            country=None,
            limit=5,
        )

        self.assertEqual(candidates, [])


class TavilyCompanyDiscoveryProviderTests(unittest.TestCase):
    """Integration-style provider tests using fake Tavily client and fake LLM only."""

    def test_provider_returns_normalized_discovery_provider_candidate(self) -> None:
        search_responses = {
            "Foodforecast": [
                {
                    "title": (
                        "German AI FoodTech startup Foodforecast raises €8 million "
                        "to tackle ultra-fresh food wastage"
                    ),
                    "url": "https://eu-startups.com/2026/01/foodforecast-raises-8m",
                    "content": (
                        "German AI FoodTech startup Foodforecast raises €8 million "
                        "to tackle ultra-fresh food wastage."
                    ),
                    "score": 0.95,
                }
            ],
            "Foodforecast official website": [
                {
                    "title": "Foodforecast | Official Website",
                    "url": "https://foodforecast.com/about",
                    "content": "Foodforecast AI demand forecasting software.",
                    "score": 0.98,
                }
            ],
        }
        fake_client = FakeTavilyClient(search_responses=search_responses)
        fake_llm = FakeLLMExtractor(
            {
                "is_company_mention": True,
                "company_name": "Foodforecast",
                "description": "AI demand forecasting software for fresh food.",
                "confidence": 0.95,
            }
        )
        provider = TavilyCompanyDiscoveryProvider(
            client=fake_client,
            llm=fake_llm,
            perform_website_lookup=True,
        )

        candidates = provider.discover(
            query="Foodforecast",
            sector="Food Technology",
            country="Germany",
            limit=5,
        )

        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate.company_name, "Foodforecast")
        self.assertEqual(candidate.website, "https://foodforecast.com")
        self.assertEqual(
            candidate.evidence_url,
            "https://eu-startups.com/2026/01/foodforecast-raises-8m",
        )
        self.assertEqual(candidate.provider, "tavily")
        self.assertEqual(
            candidate.provider_metadata["extraction_method"],
            "gemini_structured",
        )

    def test_provider_respects_limit(self) -> None:
        results = [
            {
                "title": f"Startup {name} raises funding round",
                "url": f"https://news-{index}.example.com/{name.lower()}",
                "content": f"{name} is an AI company building enterprise tools.",
                "score": 0.9,
            }
            for index, name in enumerate(["AlphaCorp", "BetaCorp", "GammaCorp"], start=1)
        ]
        fake_client = FakeTavilyClient(results=results)

        def llm_factory(items: list[dict[str, str]]) -> list[dict[str, Any]]:
            title = items[0]["title"]
            for name in ("AlphaCorp", "BetaCorp", "GammaCorp"):
                if name in title:
                    return [
                        {
                            "is_company_mention": True,
                            "company_name": name,
                            "confidence": 0.95,
                        }
                    ]
            return []

        provider = TavilyCompanyDiscoveryProvider(
            client=fake_client,
            llm=llm_factory,
            perform_website_lookup=False,
        )

        with unittest.mock.patch.object(
            provider,
            "_lookup_official_website",
            side_effect=lambda company_name, evidence_url, evidence_domain: (
                f"https://{company_name.lower()}.com",
                f"{company_name.lower()}.com",
            ),
        ):
            candidates = provider.discover(
                query="AI companies",
                sector=None,
                country=None,
                limit=2,
            )

        self.assertEqual(len(candidates), 2)

    def test_provider_rejects_duplicate_domains(self) -> None:
        fake_client = FakeTavilyClient(
            results=[
                {
                    "title": "First article about AcmeAI",
                    "url": "https://industry-news.example.com/acme-1",
                    "content": "AcmeAI builds automation software.",
                    "score": 0.91,
                },
                {
                    "title": "Second article about AcmeAI",
                    "url": "https://industry-news.example.com/acme-2",
                    "content": "AcmeAI expands into Europe.",
                    "score": 0.89,
                },
            ]
        )
        fake_llm = FakeLLMExtractor(
            {
                "is_company_mention": True,
                "company_name": "AcmeAI",
                "confidence": 0.95,
            }
        )
        provider = TavilyCompanyDiscoveryProvider(
            client=fake_client,
            llm=fake_llm,
            perform_website_lookup=False,
        )

        with unittest.mock.patch.object(
            provider,
            "_lookup_official_website",
            return_value=("https://acmeai.com", "acmeai.com"),
        ):
            candidates = provider.discover(query="AcmeAI", sector=None, country=None, limit=5)

        self.assertLessEqual(len(candidates), 1)
        self.assertGreaterEqual(provider.last_stats.provider_duplicate, 1)

    def test_provider_rejects_non_company_domains_as_official_website(self) -> None:
        fake_client = FakeTavilyClient(
            search_responses={
                "TrendCo": [
                    {
                        "title": "TrendCo launches new analytics platform",
                        "url": "https://forbes.com/sites/trendco-launch",
                        "content": "TrendCo launched a new analytics platform.",
                        "score": 0.88,
                    }
                ],
                "TrendCo official website": [
                    {
                        "title": "PMC academic paper",
                        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC11488428",
                        "content": "Academic research article.",
                        "score": 0.95,
                    }
                ],
            }
        )
        fake_llm = FakeLLMExtractor(
            {
                "is_company_mention": True,
                "company_name": "TrendCo",
                "confidence": 0.95,
            }
        )
        provider = TavilyCompanyDiscoveryProvider(
            client=fake_client,
            llm=fake_llm,
            perform_website_lookup=True,
        )

        candidates = provider.discover(query="TrendCo", sector=None, country=None, limit=5)

        self.assertEqual(candidates, [])
        self.assertGreater(provider.last_stats.missing_url, 0)

    def test_provider_rejects_generic_listicle_titles(self) -> None:
        fake_client = FakeTavilyClient(
            results=[
                {
                    "title": "Best AI Startups in Germany (2026)",
                    "url": "https://seedtable.com/best-ai-startups-in-germany",
                    "content": "A list of the best AI startups in Germany.",
                    "score": 0.92,
                }
            ]
        )
        provider = TavilyCompanyDiscoveryProvider(
            client=fake_client,
            llm=FakeLLMExtractor([]),
            perform_website_lookup=False,
        )

        candidates = provider.discover(
            query="AI startups",
            sector=None,
            country=None,
            limit=5,
        )

        self.assertEqual(candidates, [])
        self.assertGreater(provider.last_stats.unrelated_article, 0)

    def test_provider_rejects_missing_urls(self) -> None:
        fake_client = FakeTavilyClient(
            results=[
                {
                    "title": "Company without URL",
                    "url": "",
                    "content": "Missing URL content.",
                    "score": 0.75,
                }
            ]
        )
        provider = TavilyCompanyDiscoveryProvider(
            client=fake_client,
            llm=FakeLLMExtractor([]),
            perform_website_lookup=False,
        )

        candidates = provider.discover(query="AI", sector=None, country=None, limit=5)

        self.assertEqual(candidates, [])
        self.assertGreater(provider.last_stats.missing_url, 0)

    def test_gemini_structured_extraction_returns_company_not_article_title(self) -> None:
        article_title = (
            "German AI FoodTech startup Foodforecast raises €8 million "
            "to tackle ultra-fresh food wastage"
        )
        fake_client = FakeTavilyClient(
            results=[
                {
                    "title": article_title,
                    "url": "https://eu-startups.com/2026/01/foodforecast-raises-8m",
                    "content": article_title,
                    "score": 0.95,
                }
            ]
        )
        fake_llm = FakeLLMExtractor(
            {
                "is_company_mention": True,
                "company_name": "Foodforecast",
                "confidence": 0.95,
            }
        )
        provider = TavilyCompanyDiscoveryProvider(
            client=fake_client,
            llm=fake_llm,
            perform_website_lookup=False,
        )

        with unittest.mock.patch.object(
            provider,
            "_lookup_official_website",
            return_value=("https://foodforecast.com", "foodforecast.com"),
        ):
            candidates = provider.discover(
                query="Foodforecast",
                sector="Food Technology",
                country="Germany",
                limit=5,
            )

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].company_name, "Foodforecast")
        self.assertNotEqual(candidates[0].company_name, article_title)

    def test_gemini_failure_never_falls_back_to_tavily_title(self) -> None:
        article_title = "Some Unknown Web Page Title"
        fake_client = FakeTavilyClient(
            results=[
                {
                    "title": article_title,
                    "url": "https://example.com/page",
                    "content": "Content snippet.",
                    "score": 0.8,
                }
            ]
        )
        provider = TavilyCompanyDiscoveryProvider(
            client=fake_client,
            llm=FakeLLMExtractor(should_fail=True),
            perform_website_lookup=False,
        )

        candidates = provider.discover(query="AI", sector=None, country=None, limit=5)

        self.assertEqual(candidates, [])
        self.assertGreater(provider.last_stats.no_company_name_extracted, 0)
        for candidate in candidates:
            self.assertNotEqual(candidate.company_name, article_title)

    def test_provider_maps_authentication_error(self) -> None:
        fake_client = FakeTavilyClient(error=TavilyAuthenticationError("Invalid API Key"))
        provider = TavilyCompanyDiscoveryProvider(
            client=fake_client,
            perform_website_lookup=False,
        )

        with self.assertRaises(DiscoveryProviderAuthenticationError):
            provider.discover(query="AI", sector=None, country=None, limit=5)

    def test_provider_maps_configuration_error(self) -> None:
        fake_client = FakeTavilyClient(
            error=TavilyConfigurationError("TAVILY_API_KEY missing")
        )
        provider = TavilyCompanyDiscoveryProvider(
            client=fake_client,
            perform_website_lookup=False,
        )

        with self.assertRaises(DiscoveryProviderConfigurationError):
            provider.discover(query="AI", sector=None, country=None, limit=5)

    def test_provider_maps_rate_limit_error(self) -> None:
        fake_client = FakeTavilyClient(error=TavilyRateLimitError("Rate limit exceeded"))
        provider = TavilyCompanyDiscoveryProvider(
            client=fake_client,
            perform_website_lookup=False,
        )

        with self.assertRaises(DiscoveryProviderRateLimitError):
            provider.discover(query="AI", sector=None, country=None, limit=5)


class TavilyDiscoveryRelevanceTests(unittest.TestCase):
    """Relevance guardrails for sector/country/query constrained discovery."""

    DISCOVERY_QUERY = "AI food technology startups Germany"
    DISCOVERY_SECTOR = "Food Technology"
    DISCOVERY_COUNTRY = "Germany"

    def _make_provider(
        self,
        *,
        results: list[dict[str, object]] | None = None,
        llm_response: dict[str, Any] | str | None = None,
        search_responses: dict[str, list[dict[str, object]]] | None = None,
    ) -> TavilyCompanyDiscoveryProvider:
        return TavilyCompanyDiscoveryProvider(
            client=FakeTavilyClient(results=results, search_responses=search_responses),
            llm=FakeLLMExtractor(llm_response or {}),
            perform_website_lookup=False,
        )

    def test_case_1_rejects_anthropic_for_foodtech_germany(self) -> None:
        provider = self._make_provider(
            results=[
                {
                    "title": "Anthropic Claude AI assistant",
                    "url": "https://claude.ai",
                    "content": "Anthropic builds Claude, a general-purpose AI assistant.",
                    "score": 0.9,
                }
            ],
            llm_response={
                "is_company_mention": True,
                "company_name": "Anthropic",
                "matches_query": True,
                "matches_sector": False,
                "matches_country": False,
                "confidence": 0.95,
            },
        )

        candidates = provider.discover(
            query=self.DISCOVERY_QUERY,
            sector=self.DISCOVERY_SECTOR,
            country=self.DISCOVERY_COUNTRY,
            limit=5,
        )

        self.assertEqual(candidates, [])
        self.assertGreater(provider.last_stats.irrelevant_candidate, 0)

    def test_case_2_accepts_foodforecast_for_foodtech_germany(self) -> None:
        provider = self._make_provider(
            results=[
                {
                    "title": (
                        "German AI FoodTech startup Foodforecast raises EUR 8 million"
                    ),
                    "url": "https://eu-startups.com/2026/01/foodforecast-raises-8m",
                    "content": (
                        "German AI FoodTech startup Foodforecast raises EUR 8 million "
                        "to tackle food waste in Germany."
                    ),
                    "score": 0.95,
                }
            ],
            llm_response={
                "is_company_mention": True,
                "company_name": "Foodforecast",
                "matches_query": True,
                "matches_sector": True,
                "matches_country": True,
                "confidence": 0.95,
            },
        )

        with unittest.mock.patch.object(
            provider,
            "_lookup_official_website",
            return_value=("https://foodforecast.com", "foodforecast.com"),
        ):
            candidates = provider.discover(
                query=self.DISCOVERY_QUERY,
                sector=self.DISCOVERY_SECTOR,
                country=self.DISCOVERY_COUNTRY,
                limit=5,
            )

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].company_name, "Foodforecast")

    def test_case_3_rejects_openai_for_foodtech_discovery(self) -> None:
        provider = self._make_provider(
            results=[
                {
                    "title": "OpenAI platform overview",
                    "url": "https://openai.com/platform",
                    "content": "OpenAI provides general artificial intelligence models.",
                    "score": 0.92,
                }
            ],
            llm_response={
                "is_company_mention": True,
                "company_name": "OpenAI",
                "matches_query": False,
                "matches_sector": False,
                "matches_country": False,
                "confidence": 0.95,
            },
        )

        candidates = provider.discover(
            query=self.DISCOVERY_QUERY,
            sector=self.DISCOVERY_SECTOR,
            country=self.DISCOVERY_COUNTRY,
            limit=5,
        )

        self.assertEqual(candidates, [])
        self.assertGreater(provider.last_stats.irrelevant_candidate, 0)

    def test_case_4_rejects_foodtech_company_with_wrong_country(self) -> None:
        provider = self._make_provider(
            results=[
                {
                    "title": "US FoodTech startup FreshBite expands nationally",
                    "url": "https://example-news.com/freshbite-us",
                    "content": (
                        "FreshBite, a US food technology startup, expands across "
                        "California and Texas."
                    ),
                    "score": 0.9,
                }
            ],
            llm_response={
                "is_company_mention": True,
                "company_name": "FreshBite",
                "matches_query": True,
                "matches_sector": True,
                "matches_country": False,
                "confidence": 0.95,
            },
        )

        candidates = provider.discover(
            query=self.DISCOVERY_QUERY,
            sector=self.DISCOVERY_SECTOR,
            country=self.DISCOVERY_COUNTRY,
            limit=5,
        )

        self.assertEqual(candidates, [])
        self.assertGreater(provider.last_stats.irrelevant_candidate, 0)

    def test_case_5_does_not_require_matches_sector_when_sector_not_supplied(self) -> None:
        provider = self._make_provider(
            results=[
                {
                    "title": "OpenAI launches new model",
                    "url": "https://example-news.com/openai-model",
                    "content": "OpenAI launched a new general AI model.",
                    "score": 0.9,
                }
            ],
            llm_response={
                "is_company_mention": True,
                "company_name": "OpenAI",
                "confidence": 0.95,
            },
        )

        with unittest.mock.patch.object(
            provider,
            "_lookup_official_website",
            return_value=("https://openai.com", "openai.com"),
        ):
            candidates = provider.discover(
                query="AI companies",
                sector=None,
                country=None,
                limit=5,
            )

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].company_name, "OpenAI")

    def test_case_6_does_not_require_matches_country_when_country_not_supplied(self) -> None:
        provider = self._make_provider(
            results=[
                {
                    "title": "Foodforecast expands forecasting platform",
                    "url": "https://example-news.com/foodforecast",
                    "content": "Foodforecast expands its food forecasting platform.",
                    "score": 0.9,
                }
            ],
            llm_response={
                "is_company_mention": True,
                "company_name": "Foodforecast",
                "confidence": 0.95,
            },
        )

        with unittest.mock.patch.object(
            provider,
            "_lookup_official_website",
            return_value=("https://foodforecast.com", "foodforecast.com"),
        ):
            candidates = provider.discover(
                query="food technology startups",
                sector="Food Technology",
                country=None,
                limit=5,
            )

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].company_name, "Foodforecast")

    def test_case_7_brand_ai_company_name_passes_syntax_validation(self) -> None:
        provider = TavilyCompanyDiscoveryProvider(
            client=FakeTavilyClient(),
            llm=FakeLLMExtractor([]),
            perform_website_lookup=False,
        )
        self.assertTrue(provider._is_valid_company_name("Perplexity AI"))
        self.assertFalse(provider._is_valid_company_name("AI"))
        self.assertFalse(provider._is_valid_company_name("Platform"))

    def test_case_8_malformed_gemini_output_remains_fail_closed(self) -> None:
        provider = self._make_provider(
            results=[
                {
                    "title": "Some article",
                    "url": "https://example.com/article",
                    "content": "German food technology startup mentioned here.",
                    "score": 0.8,
                }
            ],
            llm_response="NOT VALID JSON OUTPUT",
        )

        candidates = provider.discover(
            query=self.DISCOVERY_QUERY,
            sector=self.DISCOVERY_SECTOR,
            country=self.DISCOVERY_COUNTRY,
            limit=5,
        )

        self.assertEqual(candidates, [])
        self.assertGreater(provider.last_stats.no_company_name_extracted, 0)

    def test_case_9_tavily_title_never_becomes_company_name(self) -> None:
        article_title = "German food tech company secures EUR 8 million"
        provider = self._make_provider(
            results=[
                {
                    "title": article_title,
                    "url": "https://example.com/news/food-tech",
                    "content": (
                        "German food tech company secures EUR 8 million in Germany."
                    ),
                    "score": 0.9,
                }
            ],
            llm_response={
                "is_company_mention": True,
                "company_name": article_title,
                "matches_query": True,
                "matches_sector": True,
                "matches_country": True,
                "confidence": 0.99,
            },
        )

        candidates = provider.discover(
            query=self.DISCOVERY_QUERY,
            sector=self.DISCOVERY_SECTOR,
            country=self.DISCOVERY_COUNTRY,
            limit=5,
        )

        self.assertEqual(candidates, [])
        self.assertGreater(provider.last_stats.blocked_generic_name, 0)

    def test_case_10_langchain_content_block_regression_with_relevance_fields(self) -> None:
        llm = FakeLangChainLLM(
            content=[
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "is_company_mention": True,
                            "company_name": "Foodforecast",
                            "description": "AI-powered food forecasting company.",
                            "matches_query": True,
                            "matches_sector": True,
                            "matches_country": True,
                            "confidence": 0.95,
                        }
                    ),
                    "extras": {"signature": "fake-signature"},
                }
            ]
        )
        provider = TavilyCompanyDiscoveryProvider(
            client=FakeTavilyClient(),
            llm=llm,
            perform_website_lookup=False,
        )

        records, method = provider._extract_companies_with_gemini(
            [
                {
                    "title": "German FoodTech startup Foodforecast",
                    "url": "https://example.com/foodforecast",
                    "content": "Foodforecast is a German food technology startup.",
                }
            ]
        )

        self.assertEqual(method, "gemini_structured")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["company_name"], "Foodforecast")


if __name__ == "__main__":
    unittest.main()
