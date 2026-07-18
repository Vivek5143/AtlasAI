"""NewsAPI client wrapper."""

from __future__ import annotations

import json
from datetime import datetime, timezone
import logging
from typing import Any
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request

try:
    import requests  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - fallback for environments without requests
    requests = None

from app.config.settings import settings


class NewsApiClientError(Exception):
    """Base class for NewsAPI client errors."""


class NewsApiConfigurationError(NewsApiClientError):
    """Raised when required NewsAPI settings are missing."""


class NewsApiAuthenticationError(NewsApiClientError):
    """Raised when NewsAPI credentials are invalid."""


class NewsApiRateLimitError(NewsApiClientError):
    """Raised when NewsAPI rate limits are exceeded."""


class NewsApiRequestError(NewsApiClientError):
    """Raised when NewsAPI cannot be reached."""


class NewsApiResponseError(NewsApiClientError):
    """Raised when NewsAPI returns malformed or unexpected payloads."""


class NewsApiClient:
    """Client wrapper around the NewsAPI HTTP API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://newsapi.org/v2",
        timeout: float = 12.0,
        logger: logging.Logger | None = None,
    ) -> None:
        self.api_key = api_key or settings.NEWS_API_KEY
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @staticmethod
    def _normalize_datetime(value: str | None) -> datetime | None:
        """Normalize timestamp strings from NewsAPI payloads."""

        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed

    def _normalize_article(
        self,
        article: dict[str, Any],
        query: str | None = None,
    ) -> dict[str, Any]:
        """Normalize a NewsAPI article payload into a stable dictionary."""

        source = article.get("source") if isinstance(article.get("source"), dict) else {}
        return {
            "query": query,
            "source_name": source.get("name"),
            "title": article.get("title"),
            "url": article.get("url"),
            "published_at": self._normalize_datetime(article.get("publishedAt")),
            "description": article.get("description"),
            "content": article.get("content"),
            "author": article.get("author"),
            "image_url": article.get("urlToImage"),
            "raw": article,
        }

    def _build_payload_from_http_error(self, body_text: str) -> dict[str, Any]:
        """Attempt to parse NewsAPI error payload."""

        if not body_text:
            return {}
        try:
            payload = json.loads(body_text)
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}

    def _raise_for_error_payload(
        self,
        *,
        endpoint: str,
        payload: dict[str, Any],
        status_code: int | None = None,
    ) -> None:
        """Raise typed errors based on NewsAPI response payload."""

        if payload.get("status") != "error":
            return

        code = str(payload.get("code") or "")
        message = str(payload.get("message") or "NewsAPI request failed.")
        log_context = {
            "endpoint": endpoint,
            "status_code": status_code,
            "error_code": code,
        }

        if status_code in {401, 403} or code in {"apiKeyInvalid", "apiKeyMissing"}:
            self.logger.warning("NewsAPI authentication failed.", extra=log_context)
            raise NewsApiAuthenticationError("News provider authentication failed.")

        if status_code == 429 or code == "rateLimited":
            self.logger.warning("NewsAPI rate limit reached.", extra=log_context)
            raise NewsApiRateLimitError("News provider rate limit reached. Please retry later.")

        self.logger.warning("NewsAPI returned an error payload.", extra=log_context)
        raise NewsApiResponseError(message)

    def _perform_request_with_requests(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        """Execute request using requests when available."""

        if requests is None:  # pragma: no cover - defensive check
            raise NewsApiRequestError("The requests dependency is unavailable.")

        try:
            response = requests.get(url, params=params, timeout=self.timeout)
        except requests.exceptions.RequestException as exc:
            raise NewsApiRequestError("Failed to reach the news provider.") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise NewsApiResponseError("News provider returned invalid JSON.") from exc
        if not isinstance(payload, dict):
            raise NewsApiResponseError("News provider returned an invalid payload format.")

        self._raise_for_error_payload(endpoint=url, payload=payload, status_code=response.status_code)

        if response.status_code >= 400:
            raise NewsApiResponseError("News provider request failed.")
        return payload

    def _perform_request_with_urllib(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        """Execute request using urllib fallback."""

        request_url = f"{url}?{urllib_parse.urlencode(params)}"

        try:
            with urllib_request.urlopen(request_url, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
                status_code = getattr(response, "status", 200)
        except urllib_error.HTTPError as exc:
            body_text = ""
            try:
                body_text = exc.read().decode("utf-8")
            except (UnicodeDecodeError, ValueError):  # pragma: no cover - defensive decode guard
                body_text = ""
            payload = self._build_payload_from_http_error(body_text)
            self._raise_for_error_payload(endpoint=url, payload=payload, status_code=exc.code)
            raise NewsApiResponseError(f"News provider returned HTTP {exc.code}.") from exc
        except urllib_error.URLError as exc:
            raise NewsApiRequestError("Failed to reach the news provider.") from exc

        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            raise NewsApiResponseError("News provider returned invalid JSON.") from exc
        if not isinstance(payload, dict):
            raise NewsApiResponseError("News provider returned an invalid payload format.")
        self._raise_for_error_payload(endpoint=url, payload=payload, status_code=status_code)
        return payload

    def _request(self, endpoint: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        """Execute a NewsAPI request and normalize the article payloads."""

        if not self.api_key:
            raise NewsApiConfigurationError("NEWS_API_KEY is not configured on the backend.")

        safe_params = {**params}
        request_url = f"{self.base_url}/{endpoint.lstrip('/')}"
        request_params = {**params, "apiKey": self.api_key}

        self.logger.info(
            "Requesting NewsAPI endpoint.",
            extra={"endpoint": endpoint, "params": safe_params},
        )

        if requests is not None:
            payload = self._perform_request_with_requests(request_url, request_params)
        else:
            payload = self._perform_request_with_urllib(request_url, request_params)

        articles = payload.get("articles", [])
        if not isinstance(articles, list):
            raise NewsApiResponseError("News provider payload did not include an articles list.")

        query = params.get("q") if isinstance(params.get("q"), str) else None
        return [
            self._normalize_article(article, query=query)
            for article in articles
            if isinstance(article, dict)
        ]

    @staticmethod
    def _build_market_intelligence_query(
        company_name: str,
        keywords: list[str],
    ) -> str:
        """Build a NewsAPI-compatible boolean query focused on market intelligence."""

        normalized_keywords = [keyword.strip() for keyword in keywords if keyword.strip()]
        if not normalized_keywords:
            return f"\"{company_name}\""

        keyword_query = " OR ".join(
            f"\"{keyword}\"" if " " in keyword else keyword
            for keyword in normalized_keywords
        )
        return f"\"{company_name}\" AND ({keyword_query})"

    def fetch_company_news(
        self,
        company_name: str,
        *,
        from_date: datetime | None = None,
        page_size: int = 10,
        market_keywords: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch company-specific news articles from the everything endpoint."""

        trimmed_name = company_name.strip()
        if not trimmed_name:
            return []

        keywords = market_keywords or [
            value.strip()
            for value in settings.NEWS_SYNC_MARKET_KEYWORDS.split(",")
            if value.strip()
        ]
        query = self._build_market_intelligence_query(trimmed_name, keywords)

        params: dict[str, Any] = {
            "qInTitle": trimmed_name,
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": page_size,
            "searchIn": "title,description,content",
        }
        if from_date is not None:
            params["from"] = from_date.astimezone(timezone.utc).date().isoformat()
        return self._request("everything", params)

    def fetch_everything(
        self,
        query: str,
        *,
        from_date: datetime | None = None,
        page_size: int = 20,
    ) -> list[dict[str, Any]]:
        """Fetch articles matching a query from the NewsAPI everything endpoint."""

        params: dict[str, Any] = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": page_size,
        }
        if from_date is not None:
            params["from"] = from_date.astimezone(timezone.utc).date().isoformat()
        return self._request("everything", params)

    def fetch_sector_news(
        self,
        sector_name: str,
        *,
        from_date: datetime | None = None,
        page_size: int = 20,
    ) -> list[dict[str, Any]]:
        """Backward-compatible sector search helper."""

        return self.fetch_everything(sector_name, from_date=from_date, page_size=page_size)

    def fetch_latest(self, *, page_size: int = 20) -> list[dict[str, Any]]:
        """Fetch the latest general news articles."""

        return self._request(
            "top-headlines",
            {
                "language": "en",
                "pageSize": page_size,
            },
        )
