"""Gemini-backed RAG chat service for AtlasAI."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from time import perf_counter
from typing import Any
from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI
from sqlalchemy.orm import Session

from app.ai import (
    ChatGenerationError,
    EmptyVectorStoreError,
    MissingConfigurationError,
    RetrievedChunk,
    RetrievalError,
)
from app.ai.ingest import PostgresVectorIngestionService
from app.ai.prompts import build_rag_messages
from app.ai.retriever import SemanticRetrieverService
from app.ai.vector_store import ChromaVectorStoreService
from app.config.settings import settings


@dataclass(slots=True, frozen=True)
class AskAIResult:
    """Structured result returned by the RAG chat pipeline.

    Attributes:
        answer: Final natural-language answer.
        retrieved_documents: Retrieved supporting chunks.
        metadata: Metadata extracted from retrieved chunks.
        citations: Human-readable source citations.
    """

    answer: str
    retrieved_documents: list[RetrievedChunk]
    metadata: list[dict[str, Any]]
    citations: list[str]

@lru_cache(maxsize=1)
def get_gemini_llm() -> ChatGoogleGenerativeAI:
    """Create and cache the Gemini client once per process."""

    api_key = settings.EFFECTIVE_GOOGLE_API_KEY

    if not api_key:
        raise MissingConfigurationError(
            "GOOGLE_API_KEY or GEMINI_API_KEY must be configured."
        )

    return ChatGoogleGenerativeAI(
        model=settings.GOOGLE_MODEL_NAME,
        google_api_key=api_key,
        temperature=0,
    )

class AtlasAIRAGChatService:
    """Run retrieval-augmented Gemini chat over AtlasAI data."""

    def __init__(
        self,
        session: Session,
        vector_store: ChromaVectorStoreService | None = None,
        retriever: SemanticRetrieverService | None = None,
        indexer: PostgresVectorIngestionService | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize the RAG chat service.

        Args:
            session: Active SQLAlchemy session.
            vector_store: Optional vector store override.
            retriever: Optional retriever override.
            indexer: Optional indexer override.
            logger: Optional logger instance.
        """

        self.session = session
        self.vector_store = vector_store or ChromaVectorStoreService()
        self.retriever = retriever or SemanticRetrieverService(vector_store=self.vector_store)
        self.indexer = indexer or PostgresVectorIngestionService(
            session=session,
            vector_store=self.vector_store,
        )
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._llm: ChatGoogleGenerativeAI | None = None

    def _get_llm(self) -> ChatGoogleGenerativeAI:
        """Return cached Gemini client."""
        return get_gemini_llm()

    @staticmethod
    def _build_context(chunks: list[RetrievedChunk]) -> str:
        """Build the LLM context block from retrieved chunks.

        Args:
            chunks: Retrieved semantic chunks.

        Returns:
            str: Concatenated context block with source labels.
        """

        context_blocks: list[str] = []
        for index, chunk in enumerate(chunks, start=1):
            title = chunk.metadata.get("title") or "Untitled"
            source = chunk.metadata.get("source") or "unknown"
            context_blocks.append(
                f"[{index}] source={source} | title={title}\n{chunk.page_content}"
            )
        return "\n\n".join(context_blocks)

    @staticmethod
    def _build_citations(chunks: list[RetrievedChunk]) -> list[str]:
        """Build source citation labels for the API response.

        Args:
            chunks: Retrieved semantic chunks.

        Returns:
            list[str]: Human-readable source citations.
        """

        citations: list[str] = []
        for index, chunk in enumerate(chunks, start=1):
            source = chunk.metadata.get("source") or "unknown"
            title = chunk.metadata.get("title") or "Untitled"
            citations.append(f"[{index}] {title} ({source})")
        return citations

    def _normalize_metadata(self, chunks: list[RetrievedChunk]) -> list[dict[str, Any]]:
        """Normalize retrieved metadata for API serialization.

        Args:
            chunks: Retrieved semantic chunks.

        Returns:
            list[dict[str, Any]]: Serializable metadata payloads.
        """

        normalized_metadata: list[dict[str, Any]] = []
        for chunk in chunks:
            payload = dict(chunk.metadata)
            payload["score"] = chunk.score
            normalized_metadata.append(payload)
        return normalized_metadata

    def _ensure_index_ready(self) -> None:
        """Ensure the Chroma collection exists and contains indexed content.

        Raises:
            EmptyVectorStoreError: If indexing completes with no documents.
        """

        self.vector_store.initialize()
        if self.vector_store.document_count() > 0:
            return

        self.logger.info("ChromaDB is empty; indexing PostgreSQL content before answering.")
        summary = self.indexer.index_all()
        if summary.get("total", 0) == 0:
            raise EmptyVectorStoreError(
                "AtlasAI has no indexed documents available for retrieval."
            )

    @staticmethod
    def _coerce_llm_content(content: Any) -> str:
        """Normalize Gemini response content into a plain string."""

        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                text = getattr(item, "text", None)
                if text:
                    parts.append(str(text))
            return "\n".join(parts).strip()

        return str(content).strip()

    def ask(
        self,
        question: str,
        top_k: int | None = None,
    ):
        """Answer a user question using AtlasAI's RAG pipeline.

        Args:
            question: User question.
            top_k: Number of retrieved chunks to use.

        Returns:
            AskAIResult: Final answer with sources and metadata.

        Raises:
            MissingConfigurationError: If Gemini is not configured.
            RetrievalError: If semantic retrieval fails.
            ChatGenerationError: If Gemini generation fails.
        """
        top_k = top_k or settings.RAG_TOP_K

        if not question or not question.strip():
            raise RetrievalError("A non-empty question is required for /ask.")

        request_started_at = perf_counter()
        self._ensure_index_ready()

        retrieval_started_at = perf_counter()
        retrieved_chunks = self.retriever.retrieve(query=question.strip(), top_k=top_k)
        self.logger.info(
            "Retrieval duration for /ask: %.3f seconds.",
            perf_counter() - retrieval_started_at,
        )

        if not retrieved_chunks:
            answer = (
                "The available AtlasAI data does not contain enough information "
                "to answer that question."
            )
            return AskAIResult(
                answer=answer,
                retrieved_documents=[],
                metadata=[],
                citations=[],
            )

        context = self._build_context(retrieved_chunks)
        citations = self._build_citations(retrieved_chunks)
        metadata = self._normalize_metadata(retrieved_chunks)

        llm_started_at = perf_counter()
        try:
            response = self._get_llm().invoke(build_rag_messages(question=question, context=context))
            answer = self._coerce_llm_content(response.content)
        except MissingConfigurationError:
            raise
        except Exception as exc:  # pragma: no cover - external LLM runtime
            raise ChatGenerationError("Gemini failed to generate a response.") from exc

        self.logger.info(
            "LLM duration for /ask: %.3f seconds.",
            perf_counter() - llm_started_at,
        )
        self.logger.info(
            "Total /ask request duration: %.3f seconds.",
            perf_counter() - request_started_at,
        )

        if not answer:
            answer = (
                "The available AtlasAI data does not contain enough information "
                "to answer that question."
            )

        return AskAIResult(
            answer=answer,
            retrieved_documents=retrieved_chunks,
            metadata=metadata,
            citations=citations,
        )
