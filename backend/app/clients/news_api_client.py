"""NewsAPI client wrapper."""

from __future__ import annotations

import json
from datetime import datetime, timezone
import logging
from typing import Any
from urllib import parse as urllib_parse
from urllib import request as urllib_request

try:
    import requests  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - fallback for environments without requests
    requests = None

from app.config.settings import settings


class NewsApiClient:
    """Client wrapper around the NewsAPI HTTP API."""

    def __init__(self, api_key: str | None = None, base_url: str = "https://newsapi.org/v2", timeout: float = 10.0, logger: logging.Logger | None = None) -> None:
        """Initialize the NewsAPI client.

        Args:
            api_key: Optional API key override.
            base_url: Base NewsAPI URL.
            timeout: Request timeout in seconds.
            logger: Optional logger instance.
        """

        self.api_key = api_key or settings.NEWS_API_KEY
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def _normalize_article(self, article: dict[str, Any], query: str | None = None) -> dict[str, Any]:
        """Normalize a NewsAPI article payload into a stable dictionary."""

        published_at_raw = article.get("publishedAt")
        published_at = None
        if isinstance(published_at_raw, str) and published_at_raw:
            try:
                published_at = datetime.fromisoformat(published_at_raw.replace("Z", "+00:00"))
            except ValueError:
                published_at = None

        if published_at is not None and published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)

        source = article.get("source") or {}
        source_name = source.get("name") if isinstance(source, dict) else None

        return {
            "query": query,
            "source_name": source_name,
            "title": article.get("title"),
            "url": article.get("url"),
            "published_at": published_at,
            "description": article.get("description"),
            "content": article.get("content"),
            "author": article.get("author"),
            "raw": article,
        }

    def _request(self, endpoint: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        """Execute a NewsAPI request and normalize the article payloads."""

        if not self.api_key:
            self.logger.warning("NEWS_API_KEY is not configured; skipping NewsAPI request.")
            return []

        request_params = {**params, "apiKey": self.api_key}
        try:
            if requests is not None:
                response = requests.get(
                    f"{self.base_url}/{endpoint.lstrip('/')}",
                    params=request_params,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                payload = response.json()
            else:
                url = f"{self.base_url}/{endpoint.lstrip('/')}?{urllib_parse.urlencode(request_params)}"
                with urllib_request.urlopen(url, timeout=self.timeout) as response:
                    payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            self.logger.warning("NewsAPI request failed for endpoint '%s': %s", endpoint, exc)
            return []

        articles = payload.get("articles", []) if isinstance(payload, dict) else []
        if not isinstance(articles, list):
            return []

        query = params.get("q") if isinstance(params, dict) else None
        return [
            self._normalize_article(article, query=query)
            for article in articles
            if isinstance(article, dict)
        ]

    def fetch_everything(self, query: str) -> list[dict[str, Any]]:
        """Fetch articles matching a query from the NewsAPI everything endpoint."""

        return self._request(
            "everything",
            {
                "q": query,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 20,
            },
        )

    def fetch_company_news(self, company_name: str) -> list[dict[str, Any]]:
        """Fetch company-specific news articles."""

        return self.fetch_everything(company_name)

    def fetch_sector_news(self, sector_name: str) -> list[dict[str, Any]]:
        """Fetch sector-specific news articles."""

        return self.fetch_everything(sector_name)

    def fetch_latest(self) -> list[dict[str, Any]]:
        """Fetch the latest general news articles."""

        return self._request(
            "top-headlines",
            {
                "language": "en",
                "pageSize": 20,
            },
        )
