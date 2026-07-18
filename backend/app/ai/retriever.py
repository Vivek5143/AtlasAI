"""Semantic retriever for AtlasAI RAG queries."""

from __future__ import annotations

import logging
from time import perf_counter
from typing import Any

from app.ai import (
    EmptyVectorStoreError,
    RetrievedChunk,
    RetrievalError,
    VectorStoreError,
)
from app.ai.vector_store import ChromaVectorStoreService


class SemanticRetrieverService:
    """Retrieve semantically relevant chunks from ChromaDB."""

    NEWS_KEYWORDS = (
        "news",
        "latest news",
        "recent news",
        "recent development",
        "recent developments",
        "latest development",
        "latest developments",
        "latest article",
        "recent article",
        "recent update",
        "recent updates",
        "latest update",
        "latest updates",
        "happened recently",
    )

    COMPANY_KEYWORDS = (
        "company",
        "companies",
        "startup",
        "startups",
        "vendor",
        "vendors",
        "provider",
        "providers",
        "recommend me companies",
        "recommend companies",
        "tell me about",
        "what is",
        "who is",
    )

    PROBLEM_KEYWORDS = (
        "problem",
        "problems",
        "challenge",
        "challenges",
        "pain point",
        "pain points",
    )

    SECTOR_KEYWORDS = (
        "sector",
        "sectors",
        "industry",
        "industries",
    )

    def __init__(
        self,
        vector_store: ChromaVectorStoreService | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.vector_store = vector_store or ChromaVectorStoreService()
        self.logger = logger or logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )

    @classmethod
    def _detect_intent(cls, query: str) -> str:
        """Detect retrieval intent from the user query."""

        normalized = query.lower().strip()

        # News must have highest priority.
        if any(keyword in normalized for keyword in cls.NEWS_KEYWORDS):
            return "news"

        if any(keyword in normalized for keyword in cls.PROBLEM_KEYWORDS):
            return "problem"

        if any(keyword in normalized for keyword in cls.SECTOR_KEYWORDS):
            return "sector"

        if any(keyword in normalized for keyword in cls.COMPANY_KEYWORDS):
            return "company"

        return "general"

    @staticmethod
    def _metadata_filter_for_intent(
        intent: str,
    ) -> dict[str, Any] | None:
        """Build Chroma metadata filter."""

        filters = {
            "news": {"entity_type": "news"},
            "company": {"entity_type": "company"},
            "problem": {"entity_type": "problem"},
            "sector": {"entity_type": "sector"},
        }

        return filters.get(intent)

    def retrieve(
        self,
        query: str,
        top_k: int = 4,
    ) -> list[RetrievedChunk]:
        """Retrieve relevant AtlasAI knowledge chunks."""

        if not query or not query.strip():
            return []

        query = query.strip()

        intent = self._detect_intent(query)

        metadata_filter = self._metadata_filter_for_intent(intent)

        # Retrieve extra candidates for news.
        candidate_count = (
            max(top_k * 3, 10)
            if intent == "news"
            else top_k
        )

        self.logger.info(
            "RAG retrieval: intent=%s filter=%s candidates=%s",
            intent,
            metadata_filter,
            candidate_count,
        )

        started_at = perf_counter()

        try:
            matches = self.vector_store.search(
                query=query,
                top_k=candidate_count,
                metadata_filter=metadata_filter,
            )

        except (EmptyVectorStoreError, VectorStoreError):
            raise

        except Exception as exc:
            self.logger.exception(
                "Semantic retrieval failed for query=%r",
                query,
            )
            raise RetrievalError(
                "Semantic retrieval failed."
            ) from exc

        # Keep only requested number of final results.
        matches = matches[:top_k]

        retrieved_chunks = [
            RetrievedChunk(
                page_content=document.page_content,
                metadata=dict(document.metadata),
                score=float(score),
            )
            for document, score in matches
        ]

        self.logger.info(
            "RAG retrieval complete: "
            "intent=%s returned=%s duration=%.3fs",
            intent,
            len(retrieved_chunks),
            perf_counter() - started_at,
        )

        return retrieved_chunks