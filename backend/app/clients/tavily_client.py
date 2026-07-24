"""Tavily Search API client wrapper for company discovery."""

from __future__ import annotations

import json
import logging
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request

try:
    import requests  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover
    requests = None

from app.config.settings import settings


class TavilyClientError(Exception):
    """Base class for Tavily API client errors."""


class TavilyConfigurationError(TavilyClientError):
    """Raised when required Tavily API credentials are missing."""


class TavilyAuthenticationError(TavilyClientError):
    """Raised when Tavily credentials are invalid."""


class TavilyRateLimitError(TavilyClientError):
    """Raised when Tavily rate limits are exceeded."""


class TavilyRequestError(TavilyClientError):
    """Raised when Tavily API cannot be reached."""


class TavilyResponseError(TavilyClientError):
    """Raised when Tavily API returns malformed payloads."""


class TavilyClient:
    """
    HTTP client wrapper for Tavily Search API.

    Tavily is used only as the external company-discovery search provider.
    NewsAPI remains responsible for AtlasAI News Intelligence.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.tavily.com",
        timeout: float = 15.0,
        logger: logging.Logger | None = None,
    ) -> None:
        self.api_key = settings.TAVILY_API_KEY if api_key is None else api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.logger = logger or logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )

    def _normalize_result(
        self,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Normalize a Tavily web-search result.

        IMPORTANT:
        A Tavily result is evidence about a possible company, not necessarily
        a verified company record.

        Company-name extraction and official-domain verification should remain
        in the Discovery provider/service layer.
        """

        title = str(result.get("title") or "").strip()
        url = str(result.get("url") or "").strip()
        content = str(result.get("content") or "").strip()

        score = result.get("score")

        provider_metadata = {
            "source_url": url,
            "search_score": score,
        }

        provider_metadata = {
            key: value
            for key, value in provider_metadata.items()
            if value is not None and value != ""
        }

        return {
            "title": title,
            "url": url,
            "content": content,
            "score": score,
            "provider_metadata": provider_metadata,
        }

    def _raise_for_error_status(
        self,
        status_code: int,
        body_text: str,
    ) -> None:
        """Raise typed exceptions based on Tavily HTTP response."""

        if status_code in {401, 403}:
            self.logger.warning(
                "Tavily authentication failed (HTTP %s).",
                status_code,
            )
            raise TavilyAuthenticationError(
                "Tavily API authentication failed. Check TAVILY_API_KEY."
            )

        if status_code == 429:
            self.logger.warning("Tavily API rate limit reached.")
            raise TavilyRateLimitError(
                "Tavily API rate limit reached. Please try again later."
            )

        if status_code >= 400:
            message = (
                f"Tavily API request failed with HTTP status {status_code}."
            )

            try:
                payload = json.loads(body_text)

                if isinstance(payload, dict):
                    message = str(
                        payload.get("detail")
                        or payload.get("message")
                        or payload.get("error")
                        or message
                    )

            except json.JSONDecodeError:
                pass

            raise TavilyResponseError(message)

    def _build_company_query(
        self,
        *,
        query: str | None = None,
        sector: str | None = None,
        country: str | None = None,
    ) -> str:
        """
        Build a web-search query for company discovery.

        Example:
        query   = "AI companies"
        sector  = "Food and Beverage"
        country = "Germany"

        Result:
        "AI companies Food and Beverage Germany companies"
        """

        parts: list[str] = []

        if query and query.strip():
            parts.append(query.strip())

        combined = " ".join(parts).lower()

        if sector and sector.strip():
            sector_text = sector.strip()
            if sector_text.lower() not in combined:
                parts.append(sector_text)
                combined = " ".join(parts).lower()

        if country and country.strip():
            country_text = country.strip()
            if country_text.lower() not in combined:
                parts.append(country_text)
                combined = " ".join(parts).lower()

        # Bias toward organization/startup discovery without duplicating keywords.
        if not any(
            word in combined
            for word in ("company", "companies", "startup", "startups")
        ):
            parts.append("companies")

        return " ".join(parts).strip()

    def search_companies(
        self,
        *,
        query: str | None = None,
        sector: str | None = None,
        country: str | None = None,
        max_results: int = 10,
        search_depth: str = "basic",
    ) -> list[dict[str, Any]]:
        """
        Search Tavily for potential company candidates.

        This method returns normalized WEB SEARCH RESULTS.

        It does NOT automatically consider those results trusted companies.
        Candidate extraction/verification must happen downstream.
        """

        if not self.api_key:
            raise TavilyConfigurationError(
                "TAVILY_API_KEY is not configured on the backend."
            )

        search_query = self._build_company_query(
            query=query,
            sector=sector,
            country=country,
        )

        if not search_query:
            return []

        url = f"{self.base_url}/search"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        payload: dict[str, Any] = {
            "query": search_query,
            "search_depth": search_depth,
            "max_results": max(1, min(max_results, 20)),
            "include_answer": False,
            "include_raw_content": False,
            "include_images": False,
        }

        self.logger.info(
            "Requesting Tavily Search API for company discovery.",
            extra={
                "query": search_query,
                "sector": sector,
                "country": country,
                "max_results": max_results,
            },
        )

        json_body = json.dumps(payload)

        status_code = 200
        body_text = ""

        # ---------------------------------------------------------
        # requests implementation
        # ---------------------------------------------------------

        if requests is not None:
            try:
                response = requests.post(
                    url,
                    data=json_body,
                    headers=headers,
                    timeout=self.timeout,
                )

                status_code = response.status_code
                body_text = response.text

            except requests.exceptions.RequestException as exc:
                raise TavilyRequestError(
                    "Failed to reach Tavily API."
                ) from exc

        # ---------------------------------------------------------
        # urllib fallback
        # ---------------------------------------------------------

        else:
            req = urllib_request.Request(
                url,
                data=json_body.encode("utf-8"),
                headers=headers,
                method="POST",
            )

            try:
                with urllib_request.urlopen(
                    req,
                    timeout=self.timeout,
                ) as response:

                    status_code = getattr(
                        response,
                        "status",
                        200,
                    )

                    body_text = response.read().decode("utf-8")

            except urllib_error.HTTPError as exc:
                status_code = exc.code

                try:
                    body_text = exc.read().decode("utf-8")
                except (UnicodeDecodeError, ValueError):
                    body_text = ""

            except urllib_error.URLError as exc:
                raise TavilyRequestError(
                    "Failed to reach Tavily API."
                ) from exc

        # ---------------------------------------------------------
        # Validate HTTP response
        # ---------------------------------------------------------

        self._raise_for_error_status(
            status_code,
            body_text,
        )

        # ---------------------------------------------------------
        # Parse JSON
        # ---------------------------------------------------------

        try:
            data = json.loads(body_text)

        except json.JSONDecodeError as exc:
            raise TavilyResponseError(
                "Tavily API returned invalid JSON payload."
            ) from exc

        if not isinstance(data, dict):
            raise TavilyResponseError(
                "Tavily API response payload is not a JSON object."
            )

        results = data.get("results") or []

        if not isinstance(results, list):
            raise TavilyResponseError(
                "Tavily API response 'results' field is not a list."
            )

        # ---------------------------------------------------------
        # Normalize results
        # ---------------------------------------------------------

        normalized_results: list[dict[str, Any]] = []

        for result in results:

            if not isinstance(result, dict):
                continue

            if not result.get("url"):
                continue

            normalized = self._normalize_result(result)

            if normalized["title"] or normalized["content"]:
                normalized_results.append(normalized)

        return normalized_results