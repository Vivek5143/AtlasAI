"""Semantic retriever for AtlasAI RAG queries."""

from __future__ import annotations

import logging
from time import perf_counter

from app.ai import RetrievedChunk, RetrievalError
from app.ai.vector_store import ChromaVectorStoreService


class SemanticRetrieverService:
    """Retrieve semantically relevant chunks from ChromaDB."""

    def __init__(
        self,
        vector_store: ChromaVectorStoreService | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize the retriever service.

        Args:
            vector_store: Optional vector store override.
            logger: Optional logger instance.
        """

        self.vector_store = vector_store or ChromaVectorStoreService()
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def retrieve(self, query: str, top_k: int = 4) -> list[RetrievedChunk]:
        """Retrieve semantically similar chunks for a user question.

        Args:
            query: User question to search.
            top_k: Maximum number of chunks to return.

        Returns:
            list[RetrievedChunk]: Retrieved content, metadata, and scores.

        Raises:
            RetrievalError: If semantic retrieval fails.
        """

        if not query or not query.strip():
            return []

        started_at = perf_counter()
        try:
            matches = self.vector_store.search(query=query.strip(), top_k=top_k)
        except Exception as exc:
            if isinstance(exc, RetrievalError):
                raise
            from app.ai import EmptyVectorStoreError, VectorStoreError

            if isinstance(exc, (EmptyVectorStoreError, VectorStoreError)):
                raise
            raise RetrievalError("Semantic retrieval failed.") from exc

        retrieved_chunks = [
            RetrievedChunk(
                page_content=document.page_content,
                metadata=dict(document.metadata),
                score=float(score),
            )
            for document, score in matches
        ]

        self.logger.info(
            "Retrieved %s chunk(s) in %.3f seconds.",
            len(retrieved_chunks),
            perf_counter() - started_at,
        )
        return retrieved_chunks
