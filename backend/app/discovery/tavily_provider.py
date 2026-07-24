"""Tavily Search API + Gemini Company Discovery Provider."""

from __future__ import annotations

import json
import logging
import re
from typing import Any
from urllib.parse import urlparse

from app.clients.tavily_client import (
    TavilyAuthenticationError,
    TavilyClient,
    TavilyConfigurationError,
    TavilyRateLimitError,
    TavilyRequestError,
    TavilyResponseError,
)
from app.config.settings import settings
from app.services.company_discovery_service import (
    DiscoveryProviderAuthenticationError,
    DiscoveryProviderCandidate,
    DiscoveryProviderConfigurationError,
    DiscoveryProviderRateLimitError,
    DiscoveryProviderRequestError,
    DiscoveryProviderResponseError,
    ProviderDiscoveryStats,
    ProviderExtractionDetail,
)

NON_COMPANY_DOMAIN_EXACT = {
    "linkedin.com",
    "wikipedia.org",
    "crunchbase.com",
    "techcrunch.com",
    "forbes.com",
    "medium.com",
    "reuters.com",
    "bloomberg.com",
    "youtube.com",
    "facebook.com",
    "instagram.com",
    "x.com",
    "twitter.com",
    "github.com",
    "reddit.com",
    "substack.com",
    "glassdoor.com",
    "pitchbook.com",
    "g2.com",
    "capterra.com",
    "yumda.com",
    "duscons.com",
    "gtai.de",
    "seedtable.com",
    "eu-startups.com",
    "tech.eu",
    "ncbi.nlm.nih.gov",
    "pmc.ncbi.nlm.nih.gov",
    "nih.gov",
}

NON_COMPANY_DOMAIN_KEYWORDS = (
    "news",
    "blog",
    "magazine",
    "journal",
    "daily",
    "press",
    "media",
    "post",
    "review",
    "article",
    "publication",
    "directory",
    "startup-list",
    "startuplist",
    "listicle",
    "aggregator",
)

NON_COMPANY_DOMAIN_SUFFIXES = (".gov", ".edu", ".ac.uk")

ARTICLE_PATH_PATTERNS = (
    r"/news/",
    r"/article/",
    r"/articles/",
    r"/blog/",
    r"/publication/",
    r"/report/",
    r"/companies/",
    r"/best-",
    r"/top-",
)

GENERIC_TITLE_PATTERNS = (
    r"\btop\s+\d+\b",
    r"\b\d+\s+top\b",
    r"\b\d+\s+best\b",
    r"\bbest\s+\d+\b",
    r"\bbest\b.*\b(startups|companies)\b",
    r"\btop\b.*\b(startups|companies)\b",
    r"\blist of\b",
    r"\bcompanies to watch\b",
    r"\bstartups to watch\b",
    r"\bcompanies in\s+[a-z]+\b",
    r"\bstartups in\s+[a-z]+\b",
    r"\bartificial intelligence companies in\b",
    r"\bguide to\b",
    r"\bmastering\b",
    r"\bthe latest\b",
    r"\bon a plate\b",
    r"\bmarket report\b",
    r"\bmarket overview\b",
    r"\bindustry overview\b",
    r"\btrends\b",
    r"\btransforming\b",
    r"\(\d{4}\)",
    r"\b\d+\s+international\b.*\bcompanies\b",
    r"\btwelve\b.*\bcompanies\b",
)

HEADLINE_ACTION_VERBS = {
    "secures",
    "raises",
    "launches",
    "announces",
    "transforms",
    "transforming",
    "tackles",
    "expands",
    "acquires",
    "partners",
    "unveils",
    "combats",
    "improves",
    "masters",
    "mastering",
    "helps",
    "drives",
    "building",
    "leading",
}

GENERIC_COMPANY_WORDS = {
    "company",
    "companies",
    "startup",
    "startups",
    "report",
    "guide",
    "article",
    "news",
    "top",
    "best",
    "list",
    "technology",
    "technologies",
    "services",
    "solutions",
    "software",
    "platform",
    "ai",
    "artificial intelligence",
    "industry",
    "market",
    "sector",
    "analysis",
    "overview",
    "culinary",
    "innovation",
    "trends",
    "food",
    "foodtech",
    "greentech",
}

CORPORATE_SUFFIXES = {
    "gmbh",
    "inc",
    "corp",
    "corporation",
    "ltd",
    "limited",
    "co",
    "ag",
    "nv",
    "sa",
    "plc",
}

SECTOR_FILLER_WORDS = {
    "technology",
    "tech",
    "software",
    "digital",
    "services",
    "solutions",
    "and",
    "the",
    "industry",
    "sector",
}

SECTOR_TERM_EXPANSIONS: dict[str, tuple[str, ...]] = {
    "food": (
        "food",
        "foodtech",
        "food-tech",
        "agriculture",
        "agrifood",
        "agri-food",
        "beverage",
        "culinary",
        "grocery",
        "farming",
        "restaurant",
        "fresh food",
        "meal",
        "nutrition",
    ),
}

COUNTRY_TERM_ALIASES: dict[str, tuple[str, ...]] = {
    "germany": ("germany", "german", "deutschland", "berlin", "munich", "hamburg"),
    "france": ("france", "french", "paris"),
    "united kingdom": ("united kingdom", "uk", "british", "england", "london"),
    "usa": ("usa", "u.s.", "united states", "american"),
    "united states": ("usa", "u.s.", "united states", "american"),
}

QUERY_RELEVANCE_STOPWORDS = {
    "ai",
    "the",
    "and",
    "or",
    "in",
    "for",
    "a",
    "an",
    "to",
    "of",
    "technology",
    "technologies",
    "startup",
    "startups",
    "company",
    "companies",
    "tech",
    "software",
    "digital",
}

DIAGNOSTIC_TITLE_MAX_LENGTH = 120


class TavilyCompanyDiscoveryProvider:
    """
    Two-Stage Tavily + Gemini Company Discovery Provider.

    Pipeline:
      1. Broad Tavily search
      2. Deterministic pre-filtering
      3. Per-item Gemini structured extraction (no title fallback)
      4. Company-name validation and evidence support check
      5. Deduplication
      6. Fail-closed official website verification
      7. DiscoveryProviderCandidate assembly
    """

    def __init__(
        self,
        client: TavilyClient | None = None,
        llm: Any | None = None,
        logger: logging.Logger | None = None,
        perform_website_lookup: bool = True,
    ) -> None:
        self.client = client or TavilyClient()
        self.llm = llm
        self.logger = logger or logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )
        self.last_stats = ProviderDiscoveryStats()
        self.perform_website_lookup = perform_website_lookup
        self._active_discovery_context: dict[str, str | None] = {}

    @staticmethod
    def _coerce_optional_bool(value: Any) -> bool | None:
        if value is None:
            return None
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"false", "0", "no"}:
                return False
            if lowered in {"true", "1", "yes"}:
                return True
            return None
        return bool(value)

    def _sector_relevance_terms(self, sector: str) -> set[str]:
        terms: set[str] = set()
        for word in re.findall(r"[a-z0-9]+", sector.lower()):
            if word in SECTOR_FILLER_WORDS or len(word) < 3:
                continue
            terms.add(word)
            terms.update(SECTOR_TERM_EXPANSIONS.get(word, ()))
        return terms

    def _country_relevance_terms(self, country: str) -> set[str]:
        key = country.strip().lower()
        aliases = COUNTRY_TERM_ALIASES.get(key, (key,))
        return {alias.lower() for alias in aliases if alias}

    def _query_relevance_terms(self, query: str) -> set[str]:
        terms: set[str] = set()
        for word in re.findall(r"[a-z0-9]+", query.lower()):
            if len(word) < 4 or word in QUERY_RELEVANCE_STOPWORDS:
                continue
            terms.add(word)
        return terms

    def _deterministic_sector_match(self, sector: str, evidence: str) -> bool:
        terms = self._sector_relevance_terms(sector)
        if not terms:
            return True
        return any(term in evidence for term in terms)

    def _deterministic_country_match(self, country: str, evidence: str) -> bool:
        terms = self._country_relevance_terms(country)
        if not terms:
            return True
        return any(term in evidence for term in terms)

    def _deterministic_query_match(self, query: str, evidence: str) -> bool:
        terms = self._query_relevance_terms(query)
        if not terms:
            return True
        return any(term in evidence for term in terms)

    def _passes_discovery_relevance(
        self,
        record: dict[str, Any],
        *,
        title: str,
        content: str,
        query: str | None,
        sector: str | None,
        country: str | None,
    ) -> tuple[bool, str | None]:
        evidence = f"{title} {content}".lower()

        if query and query.strip():
            matches_query = self._coerce_optional_bool(record.get("matches_query"))
            if matches_query is False:
                return False, "query_mismatch"
            if matches_query is not True and not self._deterministic_query_match(
                query.strip(),
                evidence,
            ):
                return False, "query_mismatch"

        if sector and sector.strip():
            matches_sector = self._coerce_optional_bool(record.get("matches_sector"))
            if matches_sector is False:
                return False, "sector_mismatch"
            if matches_sector is not True and not self._deterministic_sector_match(
                sector.strip(),
                evidence,
            ):
                return False, "sector_mismatch"

        if country and country.strip():
            matches_country = self._coerce_optional_bool(record.get("matches_country"))
            if matches_country is False:
                return False, "country_mismatch"
            if matches_country is not True and not self._deterministic_country_match(
                country.strip(),
                evidence,
            ):
                return False, "country_mismatch"

        return True, None

    def _evidence_prefilter_relevance(
        self,
        *,
        title: str,
        content: str,
        query: str | None,
        sector: str | None,
        country: str | None,
    ) -> tuple[bool, str | None]:
        """Cheap deterministic gate before Gemini when constraints are supplied."""
        evidence = f"{title} {content}".lower()
        has_constraint = bool(
            (query and query.strip())
            or (sector and sector.strip())
            or (country and country.strip())
        )
        if not has_constraint:
            return True, None

        query_ok = (
            not (query and query.strip())
            or self._deterministic_query_match(query.strip(), evidence)
        )
        sector_ok = (
            not (sector and sector.strip())
            or self._deterministic_sector_match(sector.strip(), evidence)
        )
        country_ok = (
            not (country and country.strip())
            or self._deterministic_country_match(country.strip(), evidence)
        )

        if not query_ok:
            return False, "query_mismatch"
        if not sector_ok:
            return False, "sector_mismatch"
        if not country_ok:
            return False, "country_mismatch"
        return True, None

    def _build_gemini_extraction_prompt(
        self,
        item: dict[str, str],
        *,
        query: str | None,
        sector: str | None,
        country: str | None,
    ) -> str:
        discovery_context = {
            "query": query,
            "sector": sector,
            "country": country,
        }
        return (
            "You are extracting company names from web search evidence for a "
            "constrained company discovery request.\n\n"
            "Discovery request:\n"
            f"{json.dumps(discovery_context)}\n\n"
            "Extract at most ONE explicit company mentioned in the supplied "
            "search result.\n\n"
            "Rules:\n"
            "- Return an actual named company only.\n"
            "- Do NOT return the article title.\n"
            "- Do NOT return a news headline.\n"
            "- Do NOT return a listicle title.\n"
            "- Do NOT return a generic industry/topic.\n"
            "- Do NOT invent a company.\n"
            "- The company must be explicitly supported by the supplied "
            "title/content.\n"
            "- Evaluate whether the company matches the discovery request "
            "query, sector, and country using the evidence provided.\n"
            "- A well-known AI company is NOT relevant when the request is "
            "for a different sector/country (e.g. Food Technology in Germany).\n"
            "- If no specific company can be identified confidently, or the "
            "company does not match the requested discovery criteria, return "
            "is_company_mention=false and company_name=null.\n\n"
            "Return ONLY valid JSON using this structure:\n"
            "{\n"
            '  "is_company_mention": true,\n'
            '  "company_name": "Example Company",\n'
            '  "description": "Short evidence-grounded description",\n'
            '  "matches_query": true,\n'
            '  "matches_sector": true,\n'
            '  "matches_country": true,\n'
            '  "confidence": 0.95\n'
            "}\n\n"
            "Search result:\n"
            f"{json.dumps(item)}"
        )

    def _truncate_diagnostic_title(self, title: str | None) -> str | None:
        if not title:
            return None
        cleaned = re.sub(r"\s+", " ", title).strip()
        if len(cleaned) <= DIAGNOSTIC_TITLE_MAX_LENGTH:
            return cleaned
        return cleaned[: DIAGNOSTIC_TITLE_MAX_LENGTH - 3].rstrip() + "..."

    def _record_skip(
        self,
        stats: ProviderDiscoveryStats,
        *,
        title: str | None,
        source_domain: str | None,
        reason: str,
    ) -> None:
        stats.extraction_details.append(
            ProviderExtractionDetail(
                title=self._truncate_diagnostic_title(title),
                source_domain=source_domain or None,
                extraction_skip_reason=reason,
            )
        )

    def _get_domain(self, url: str | None) -> str | None:
        if not url:
            return None
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            return domain or None
        except ValueError:
            return None

    def _is_non_company_domain(self, domain: str | None) -> bool:
        if not domain:
            return True

        lowered = domain.lower()
        if any(lowered.endswith(suffix) for suffix in NON_COMPANY_DOMAIN_SUFFIXES):
            return True
        if any(
            lowered == blocked or lowered.endswith(f".{blocked}")
            for blocked in NON_COMPANY_DOMAIN_EXACT
        ):
            return True
        if "ncbi.nlm.nih.gov" in lowered or lowered.startswith("pmc."):
            return True
        return any(keyword in lowered for keyword in NON_COMPANY_DOMAIN_KEYWORDS)

    def _is_article_like_url(self, url: str) -> bool:
        try:
            path = urlparse(url).path.lower()
        except ValueError:
            return True
        if not path or path == "/":
            return False
        return any(re.search(pattern, path) for pattern in ARTICLE_PATH_PATTERNS)

    def _normalize_to_origin(self, url: str) -> str | None:
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return None
            return f"{parsed.scheme}://{parsed.netloc}"
        except ValueError:
            return None

    def _looks_generic_title(self, title: str) -> bool:
        lowered = title.lower()
        return any(
            re.search(pattern, lowered, flags=re.IGNORECASE)
            for pattern in GENERIC_TITLE_PATTERNS
        )

    def _is_headline_or_sentence(self, name: str) -> bool:
        cleaned = name.strip()
        words = cleaned.split()

        if len(words) > 6:
            return True

        lowered_words = [w.lower().strip(".,:;!?\"'()[]") for w in words]

        if any(verb in lowered_words for verb in HEADLINE_ACTION_VERBS):
            return True

        if (
            any(char in cleaned for char in ("€", "$", "£"))
            or "million" in lowered_words
            or "billion" in lowered_words
        ):
            return True

        if ":" in cleaned or "..." in cleaned or "?" in cleaned or "!" in cleaned:
            return True

        if re.search(r"\(\d{4}\)", cleaned):
            return True

        if self._looks_generic_title(cleaned):
            return True

        return False

    def _should_prefilter_title(self, title: str) -> bool:
        cleaned = title.strip()
        if not cleaned:
            return True
        return self._looks_generic_title(cleaned)

    def _is_valid_company_name(self, name: str | None) -> bool:
        if not name:
            return False
        cleaned = name.strip()
        if len(cleaned) < 2 or len(cleaned) > 80:
            return False
        if cleaned.lower() in GENERIC_COMPANY_WORDS:
            return False

        tokens = [
            token.lower().strip(".,:;!?\"'()[]")
            for token in cleaned.split()
            if token.strip(".,:;!?\"'()[]")
        ]
        meaningful = [
            token
            for token in tokens
            if token not in CORPORATE_SUFFIXES and len(token) >= 2
        ]
        if not meaningful:
            return False
        if all(token in GENERIC_COMPANY_WORDS for token in meaningful):
            return False

        if self._is_headline_or_sentence(cleaned):
            return False
        return True

    def _is_name_supported_by_evidence(self, name: str, title: str, content: str) -> bool:
        combined = f"{title} {content}".lower()
        clean_name = name.strip().lower()

        suffixes = CORPORATE_SUFFIXES
        words = [w for w in clean_name.split() if w not in suffixes]
        if not words:
            return clean_name in combined

        main_brand = " ".join(words)
        if main_brand in combined or clean_name in combined:
            return True

        compact = re.sub(r"[^a-z0-9]", "", main_brand)
        if len(compact) >= 4:
            combined_compact = re.sub(r"[^a-z0-9]", "", combined)
            return compact in combined_compact
        return False

    def _is_compatible_domain(self, company_name: str, domain: str | None) -> bool:
        if not domain or self._is_non_company_domain(domain):
            return False

        clean_name = re.sub(r"[^a-z0-9]", "", company_name.lower())
        registrable = domain.lower().split(".")[0]
        clean_domain = re.sub(r"[^a-z0-9]", "", registrable)

        if len(clean_name) < 3 or len(clean_domain) < 3:
            return False

        if clean_name == clean_domain:
            return True
        if clean_name in clean_domain or clean_domain in clean_name:
            return len(min(clean_name, clean_domain, key=len)) >= 4
        return False

    def _parse_json_payload(self, raw: str) -> Any | None:
        """Parse JSON returned by Gemini.

        Handles plain JSON as well as JSON wrapped in Markdown code fences.
        """
        if not raw:
            return None

        clean = raw.strip()

        if clean.startswith("```json"):
            clean = clean.split("```json", 1)[1].split("```", 1)[0].strip()
        elif clean.startswith("```"):
            clean = clean.split("```", 1)[1].split("```", 1)[0].strip()

        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            self.logger.debug(
                "Failed to parse Gemini extraction JSON. Raw content=%r",
                clean[:500],
            )
            return None

    def _coerce_llm_content(self, content: Any) -> str:
        """Convert Gemini/LangChain response content into plain text."""
        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, dict):
                    text = item.get("text")
                    if text:
                        parts.append(str(text))
                    continue
                text = getattr(item, "text", None)
                if text:
                    parts.append(str(text))
            return "\n".join(parts).strip()

        if content is None:
            return ""

        return str(content).strip()

    def _normalize_extraction_record(
        self,
        record: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Normalize Gemini/mock structured output. Never fall back to page title."""
        if not isinstance(record, dict):
            return None

        company_name = record.get("company_name") or record.get("name")
        if company_name is not None:
            company_name = str(company_name).strip()
        if not company_name:
            return None

        is_company = True
        if "is_company_mention" in record:
            raw_flag = record.get("is_company_mention")
            if isinstance(raw_flag, str):
                is_company = raw_flag.strip().lower() not in {"false", "0", "no"}
            else:
                is_company = bool(raw_flag)
        elif "is_company" in record:
            raw_flag = record.get("is_company")
            if isinstance(raw_flag, str):
                is_company = raw_flag.strip().lower() not in {"false", "0", "no"}
            else:
                is_company = bool(raw_flag)

        if not is_company:
            return None

        confidence = record.get("confidence")
        if confidence is not None:
            try:
                if float(confidence) < 0.5:
                    return None
            except (TypeError, ValueError):
                return None

        description = record.get("description")
        if description is not None:
            description = str(description).strip() or None

        normalized: dict[str, Any] = {
            "company_name": company_name,
            "description": description,
            "is_company": True,
        }
        for key in ("matches_query", "matches_sector", "matches_country"):
            if key in record:
                normalized[key] = record[key]
        return normalized

    def _coerce_extraction_records(
        self,
        payload: Any,
    ) -> list[dict[str, Any]]:
        if isinstance(payload, dict):
            normalized = self._normalize_extraction_record(payload)
            return [normalized] if normalized else []

        if not isinstance(payload, list):
            return []

        records: list[dict[str, Any]] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            normalized = self._normalize_extraction_record(item)
            if normalized:
                records.append(normalized)
        return records

    def _invoke_llm_for_items(
        self,
        items: list[dict[str, str]],
    ) -> Any | None:
        if self.llm is None:
            return None

        context = self._active_discovery_context
        query = context.get("query")
        sector = context.get("sector")
        country = context.get("country")
        item = items[0] if len(items) == 1 else items

        if callable(self.llm):
            return self.llm(items)

        if hasattr(self.llm, "invoke"):
            prompt = self._build_gemini_extraction_prompt(
                item if isinstance(item, dict) else {"items": items},
                query=query,
                sector=sector,
                country=country,
            )
            out = self.llm.invoke(prompt)
            return self._coerce_llm_content(getattr(out, "content", None))

        return str(self.llm)

    def _extract_companies_with_gemini(
        self,
        items: list[dict[str, str]],
    ) -> tuple[list[dict[str, Any]], str]:
        """Extract structured company records. Never uses Tavily page title."""
        if not items:
            return [], "skipped"

        if self.llm is not None:
            try:
                result = self._invoke_llm_for_items(items)

                if isinstance(result, (dict, list)):
                    records = self._coerce_extraction_records(result)
                    return records, "gemini_structured" if records else "failed"

                if isinstance(result, str):
                    parsed = self._parse_json_payload(result)
                    if parsed is None:
                        self.logger.warning(
                            "Injected LLM returned non-JSON extraction content."
                        )
                        return [], "failed"
                    records = self._coerce_extraction_records(parsed)
                    return records, "gemini_structured" if records else "failed"

                return [], "failed"
            except Exception:
                self.logger.exception("Injected LLM extraction failed")
                return [], "failed"

        if settings.EFFECTIVE_GOOGLE_API_KEY:
            try:
                from app.ai.chat import get_gemini_llm

                llm = get_gemini_llm()
                context = self._active_discovery_context
                item_payload = items[0] if len(items) == 1 else items
                prompt = self._build_gemini_extraction_prompt(
                    item_payload if isinstance(item_payload, dict) else {"items": items},
                    query=context.get("query"),
                    sector=context.get("sector"),
                    country=context.get("country"),
                )

                response = llm.invoke(prompt)
                content = self._coerce_llm_content(getattr(response, "content", None))

                if not content:
                    self.logger.warning("Gemini company extraction returned empty content.")
                    return [], "failed"

                parsed = self._parse_json_payload(content)
                if parsed is None:
                    self.logger.warning("Gemini company extraction returned non-JSON content.")
                    self.logger.debug("Gemini extraction raw content=%r", content[:500])
                    return [], "failed"

                records = self._coerce_extraction_records(parsed)
                if not records:
                    return [], "failed"
                return records, "gemini_structured"
            except Exception:
                self.logger.exception("Gemini LLM extraction failed")
                return [], "failed"

        return [], "skipped"

    def _extract_company_for_item(
        self,
        item: dict[str, Any],
    ) -> tuple[dict[str, Any] | None, str]:
        payload = [
            {
                "title": str(item.get("title") or ""),
                "url": str(item.get("url") or ""),
                "content": str(item.get("content") or ""),
            }
        ]
        records, method = self._extract_companies_with_gemini(payload)
        if method != "gemini_structured" or not records:
            return None, method
        return records[0], method

    def _verified_homepage(
        self,
        company_name: str,
        url: str,
    ) -> tuple[str | None, str | None]:
        domain = self._get_domain(url)
        if not domain or not self._is_compatible_domain(company_name, domain):
            return None, None
        if self._is_article_like_url(url):
            return None, None
        origin = self._normalize_to_origin(url)
        if not origin:
            return None, None
        return origin, domain

    def _lookup_official_website(
        self,
        company_name: str,
        evidence_url: str,
        evidence_domain: str | None,
    ) -> tuple[str | None, str | None]:
        """Lookup official website via Tavily. Never falls back to evidence_url."""
        if evidence_domain and not self._is_non_company_domain(evidence_domain):
            verified = self._verified_homepage(company_name, evidence_url)
            if verified[0]:
                return verified

        if not self.perform_website_lookup:
            return None, None

        try:
            results = self.client.search_companies(
                query=f"{company_name} official website",
                max_results=5,
            )
            for res in results:
                url = str(res.get("url") or "").strip()
                if not url:
                    continue
                verified = self._verified_homepage(company_name, url)
                if verified[0]:
                    return verified
        except Exception as exc:
            self.logger.debug(
                "Official website lookup for %s failed: %s",
                company_name,
                exc,
            )

        return None, None

    def discover(
        self,
        *,
        query: str | None,
        sector: str | None,
        country: str | None,
        limit: int,
    ) -> list[DiscoveryProviderCandidate]:
        self.last_stats = ProviderDiscoveryStats()
        self._active_discovery_context = {
            "query": query,
            "sector": sector,
            "country": country,
        }

        try:
            results = self.client.search_companies(
                query=query,
                sector=sector,
                country=country,
                max_results=max(1, min(limit * 3, 20)),
            )
        except TavilyConfigurationError as exc:
            raise DiscoveryProviderConfigurationError(str(exc)) from exc
        except TavilyAuthenticationError as exc:
            raise DiscoveryProviderAuthenticationError(str(exc)) from exc
        except TavilyRateLimitError as exc:
            raise DiscoveryProviderRateLimitError(str(exc)) from exc
        except TavilyRequestError as exc:
            raise DiscoveryProviderRequestError(str(exc)) from exc
        except TavilyResponseError as exc:
            raise DiscoveryProviderResponseError(str(exc)) from exc

        stats = ProviderDiscoveryStats(articles_fetched=len(results))
        plausible_items: list[dict[str, Any]] = []
        seen_domains: set[str] = set()

        for result in results:
            url = str(result.get("url") or "").strip()
            title = str(result.get("title") or "").strip()
            content = str(result.get("content") or "").strip()

            if not url:
                stats.missing_url += 1
                self._record_skip(
                    stats,
                    title=title,
                    source_domain=None,
                    reason="missing_url",
                )
                continue

            domain = self._get_domain(url)
            if not domain:
                stats.missing_url += 1
                self._record_skip(
                    stats,
                    title=title,
                    source_domain=None,
                    reason="missing_url",
                )
                continue

            if self._should_prefilter_title(title):
                stats.unrelated_article += 1
                self._record_skip(
                    stats,
                    title=title,
                    source_domain=domain,
                    reason="unrelated_article",
                )
                continue

            if domain in seen_domains:
                stats.provider_duplicate += 1
                self._record_skip(
                    stats,
                    title=title,
                    source_domain=domain,
                    reason="provider_duplicate",
                )
                continue

            seen_domains.add(domain)
            plausible_items.append(
                {
                    "title": title,
                    "url": url,
                    "content": content,
                    "domain": domain,
                    "score": str(result.get("score") or ""),
                }
            )

        if not plausible_items:
            self.last_stats = stats
            return []

        candidates: list[DiscoveryProviderCandidate] = []
        seen_candidate_names: set[str] = set()

        for item in plausible_items:
            prefilter_ok, prefilter_reason = self._evidence_prefilter_relevance(
                title=item["title"],
                content=item["content"],
                query=query,
                sector=sector,
                country=country,
            )
            if not prefilter_ok:
                stats.irrelevant_candidate += 1
                self._record_skip(
                    stats,
                    title=item["title"],
                    source_domain=item["domain"],
                    reason=prefilter_reason or "insufficient_relevance",
                )
                continue

            extracted_info, extraction_method = self._extract_company_for_item(item)

            if extraction_method in {"failed", "skipped"} or not extracted_info:
                stats.no_company_name_extracted += 1
                self._record_skip(
                    stats,
                    title=item["title"],
                    source_domain=item["domain"],
                    reason="no_company_name_extracted",
                )
                continue

            comp_name = str(extracted_info.get("company_name") or "").strip()
            comp_desc = extracted_info.get("description") or item.get("content")
            is_comp = bool(extracted_info.get("is_company", True))

            if not is_comp or not comp_name:
                stats.no_company_name_extracted += 1
                self._record_skip(
                    stats,
                    title=item["title"],
                    source_domain=item["domain"],
                    reason="no_company_name_extracted",
                )
                continue

            if comp_name.lower() == item["title"].strip().lower():
                stats.blocked_generic_name += 1
                self._record_skip(
                    stats,
                    title=item["title"],
                    source_domain=item["domain"],
                    reason="blocked_generic_name",
                )
                continue

            if not self._is_valid_company_name(comp_name):
                stats.blocked_generic_name += 1
                self._record_skip(
                    stats,
                    title=item["title"],
                    source_domain=item["domain"],
                    reason="blocked_generic_name",
                )
                continue

            if not self._is_name_supported_by_evidence(
                comp_name,
                item["title"],
                item["content"],
            ):
                stats.unrelated_article += 1
                self._record_skip(
                    stats,
                    title=item["title"],
                    source_domain=item["domain"],
                    reason="unrelated_article",
                )
                continue

            relevance_ok, relevance_reason = self._passes_discovery_relevance(
                extracted_info,
                title=item["title"],
                content=item["content"],
                query=query,
                sector=sector,
                country=country,
            )
            if not relevance_ok:
                stats.irrelevant_candidate += 1
                self._record_skip(
                    stats,
                    title=item["title"],
                    source_domain=item["domain"],
                    reason=relevance_reason or "insufficient_relevance",
                )
                continue

            norm_name = comp_name.strip().lower()
            if norm_name in seen_candidate_names:
                stats.provider_duplicate += 1
                self._record_skip(
                    stats,
                    title=item["title"],
                    source_domain=item["domain"],
                    reason="provider_duplicate",
                )
                continue
            seen_candidate_names.add(norm_name)

            official_url, official_domain = self._lookup_official_website(
                company_name=comp_name.strip(),
                evidence_url=item["url"],
                evidence_domain=item["domain"],
            )

            if not official_url:
                stats.missing_url += 1
                self._record_skip(
                    stats,
                    title=item["title"],
                    source_domain=item["domain"],
                    reason="missing_url",
                )
                continue

            provider_metadata = {
                "source_url": item["url"],
                "official_website_url": official_url,
                "domain": official_domain,
                "search_score": item.get("score"),
                "extraction_method": extraction_method,
            }
            provider_metadata = {
                key: value
                for key, value in provider_metadata.items()
                if value is not None and value != ""
            }

            candidates.append(
                DiscoveryProviderCandidate(
                    company_name=comp_name.strip(),
                    evidence_url=item["url"],
                    evidence_title=item["title"] or f"{comp_name} Source Profile",
                    evidence_text=comp_desc or f"{comp_name} discovered via Tavily.",
                    website=official_url,
                    country=country,
                    description=comp_desc,
                    ai_category=sector,
                    provider="tavily",
                    provider_company_id=None,
                    provider_metadata=provider_metadata,
                )
            )

            if len(candidates) >= limit:
                break

        stats.candidates_extracted = len(candidates)
        self.last_stats = stats
        return candidates
