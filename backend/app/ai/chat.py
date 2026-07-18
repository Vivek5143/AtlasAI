"""Gemini-backed RAG chat service for AtlasAI."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import logging
from time import perf_counter
from typing import Any

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
    """Structured result returned by the AtlasAI RAG pipeline."""

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
        """Initialize the AtlasAI RAG chat service."""

        self.session = session

        self.vector_store = (
            vector_store
            or ChromaVectorStoreService()
        )

        self.retriever = (
            retriever
            or SemanticRetrieverService(
                vector_store=self.vector_store
            )
        )

        self.indexer = (
            indexer
            or PostgresVectorIngestionService(
                session=session,
                vector_store=self.vector_store,
            )
        )

        self.logger = (
            logger
            or logging.getLogger(
                f"{__name__}.{self.__class__.__name__}"
            )
        )

    def _get_llm(self) -> ChatGoogleGenerativeAI:
        """Return the cached Gemini client."""

        return get_gemini_llm()

    @staticmethod
    def _build_context(
        chunks: list[RetrievedChunk],
    ) -> str:
        """Build structured context for Gemini.

        Each retrieved document receives a numbered source label
        matching the citations returned to the frontend.
        """

        context_blocks: list[str] = []

        for index, chunk in enumerate(chunks, start=1):

            metadata = chunk.metadata or {}

            title = (
                metadata.get("title")
                or "Untitled"
            )

            source = (
                metadata.get("source")
                or "unknown"
            )

            entity_type = (
                metadata.get("entity_type")
                or "unknown"
            )

            content = (
                chunk.page_content.strip()
                if chunk.page_content
                else ""
            )

            # Skip completely empty documents.
            if not content:
                continue

            context_block = (
                f"[{index}]\n"
                f"Title: {title}\n"
                f"Source: {source}\n"
                f"Entity Type: {entity_type}\n"
                f"Content:\n{content}"
            )

            context_blocks.append(
                context_block
            )

        return "\n\n".join(
            context_blocks
        )

    @staticmethod
    def _build_citations(
        chunks: list[RetrievedChunk],
    ) -> list[str]:
        """Build human-readable citations."""

        citations: list[str] = []

        for index, chunk in enumerate(
            chunks,
            start=1,
        ):

            metadata = (
                chunk.metadata
                or {}
            )

            source = (
                metadata.get("source")
                or "unknown"
            )

            title = (
                metadata.get("title")
                or "Untitled"
            )

            citations.append(
                f"[{index}] {title} ({source})"
            )

        return citations

    @staticmethod
    def _normalize_metadata(
        chunks: list[RetrievedChunk],
    ) -> list[dict[str, Any]]:
        """Normalize retrieved metadata for API serialization."""

        normalized_metadata: list[
            dict[str, Any]
        ] = []

        for chunk in chunks:

            payload = dict(
                chunk.metadata
                or {}
            )

            payload["score"] = (
                float(chunk.score)
            )

            normalized_metadata.append(
                payload
            )

        return normalized_metadata

    def _ensure_index_ready(
        self,
    ) -> None:
        """Ensure ChromaDB contains indexed AtlasAI data."""

        self.vector_store.initialize()

        document_count = (
            self.vector_store.document_count()
        )

        self.logger.info(
            "Current ChromaDB document count: %s",
            document_count,
        )

        if document_count > 0:
            return

        self.logger.info(
            "ChromaDB is empty. "
            "Indexing PostgreSQL content."
        )

        summary = (
            self.indexer.index_all()
        )

        self.logger.info(
            "Initial ChromaDB indexing summary: %s",
            summary,
        )

        if summary.get("total", 0) == 0:
            raise EmptyVectorStoreError(
                "AtlasAI has no indexed documents "
                "available for retrieval."
            )

    @staticmethod
    def _coerce_llm_content(
        content: Any,
    ) -> str:
        """Normalize Gemini response content into plain text."""

        if isinstance(
            content,
            str,
        ):
            return content.strip()

        if isinstance(
            content,
            list,
        ):

            parts: list[str] = []

            for item in content:

                # Gemini/LangChain may return dictionaries.
                if isinstance(
                    item,
                    dict,
                ):
                    text = item.get(
                        "text"
                    )

                    if text:
                        parts.append(
                            str(text)
                        )

                    continue

                # Or structured objects.
                text = getattr(
                    item,
                    "text",
                    None,
                )

                if text:
                    parts.append(
                        str(text)
                    )

            return "\n".join(
                parts
            ).strip()

        if content is None:
            return ""

        return str(
            content
        ).strip()

    def ask(
        self,
        question: str,
        top_k: int | None = None,
    ) -> AskAIResult:
        """Answer a question using AtlasAI's RAG pipeline."""

        question = (
            question.strip()
            if question
            else ""
        )

        if not question:
            raise RetrievalError(
                "A non-empty question "
                "is required for /ask."
            )

        top_k = (
            top_k
            or settings.RAG_TOP_K
        )

        request_started_at = (
            perf_counter()
        )

        # --------------------------------------------------
        # 1. Ensure vector database is ready
        # --------------------------------------------------

        self._ensure_index_ready()

        # --------------------------------------------------
        # 2. Retrieve relevant documents
        # --------------------------------------------------

        retrieval_started_at = (
            perf_counter()
        )

        retrieved_chunks = (
            self.retriever.retrieve(
                query=question,
                top_k=top_k,
            )
        )

        retrieval_duration = (
            perf_counter()
            - retrieval_started_at
        )

        self.logger.info(
            "Retrieval duration for /ask: %.3f seconds.",
            retrieval_duration,
        )

        self.logger.info(
            "Retrieved %s chunk(s) for question=%r",
            len(retrieved_chunks),
            question,
        )

        # --------------------------------------------------
        # 3. Log individual retrieved chunks
        # --------------------------------------------------

        for index, chunk in enumerate(
            retrieved_chunks,
            start=1,
        ):

            self.logger.info(
                (
                    "Retrieved chunk [%s]: "
                    "title=%r "
                    "entity_type=%r "
                    "score=%s"
                ),
                index,
                chunk.metadata.get(
                    "title"
                ),
                chunk.metadata.get(
                    "entity_type"
                ),
                chunk.score,
            )

            self.logger.debug(
                "Retrieved chunk [%s] content:\n%s",
                index,
                chunk.page_content,
            )

        # --------------------------------------------------
        # 4. Handle no retrieval results
        # --------------------------------------------------

        if not retrieved_chunks:

            answer = (
                "The available AtlasAI data does not "
                "contain enough information to answer "
                "that question."
            )

            return AskAIResult(
                answer=answer,
                retrieved_documents=[],
                metadata=[],
                citations=[],
            )

        # --------------------------------------------------
        # 5. Build context
        # --------------------------------------------------

        context = (
            self._build_context(
                retrieved_chunks
            )
        )

        citations = (
            self._build_citations(
                retrieved_chunks
            )
        )

        metadata = (
            self._normalize_metadata(
                retrieved_chunks
            )
        )

        # Important diagnostic:
        # confirms what Gemini actually receives.
        self.logger.info(
            (
                "\n"
                "========== RAG CONTEXT ==========\n"
                "QUESTION:\n%s\n\n"
                "CONTEXT:\n%s\n"
                "========== END RAG CONTEXT =========="
            ),
            question,
            context,
        )

        # If documents were retrieved but they
        # contained no usable text.
        if not context.strip():

            self.logger.warning(
                "Retrieved documents contained "
                "no usable page_content."
            )

            answer = (
                "The available AtlasAI data does not "
                "contain enough information to answer "
                "that question."
            )

            return AskAIResult(
                answer=answer,
                retrieved_documents=retrieved_chunks,
                metadata=metadata,
                citations=citations,
            )

        # --------------------------------------------------
        # 6. Build Gemini messages
        # --------------------------------------------------

        messages = (
            build_rag_messages(
                question=question,
                context=context,
            )
        )

        self.logger.info(
            "Sending %s message(s) to Gemini.",
            len(messages),
        )

        # --------------------------------------------------
        # 7. Generate answer
        # --------------------------------------------------

        llm_started_at = (
            perf_counter()
        )

        try:

            response = (
                self._get_llm().invoke(
                    messages
                )
            )

            answer = (
                self._coerce_llm_content(
                    response.content
                )
            )

            self.logger.info(
                (
                    "\n"
                    "========== GEMINI RESPONSE ==========\n"
                    "QUESTION:\n%s\n\n"
                    "ANSWER:\n%s\n"
                    "========== END GEMINI RESPONSE =========="
                ),
                question,
                answer,
            )

        except MissingConfigurationError:
            raise

        except Exception as exc:

            self.logger.exception(
                "Gemini generation failed "
                "for /ask request."
            )

            raise ChatGenerationError(
                "Gemini failed to generate "
                f"a response: "
                f"{type(exc).__name__}: {exc}"
            ) from exc

        # --------------------------------------------------
        # 8. Log timings
        # --------------------------------------------------

        llm_duration = (
            perf_counter()
            - llm_started_at
        )

        total_duration = (
            perf_counter()
            - request_started_at
        )

        self.logger.info(
            "LLM duration for /ask: %.3f seconds.",
            llm_duration,
        )

        self.logger.info(
            "Total /ask request duration: %.3f seconds.",
            total_duration,
        )

        # --------------------------------------------------
        # 9. Handle empty Gemini response
        # --------------------------------------------------

        if not answer:

            self.logger.warning(
                "Gemini returned an empty response "
                "for question=%r",
                question,
            )

            answer = (
                "The available AtlasAI data does not "
                "contain enough information to answer "
                "that question."
            )

        # --------------------------------------------------
        # 10. Return final structured result
        # --------------------------------------------------

        return AskAIResult(
            answer=answer,
            retrieved_documents=retrieved_chunks,
            metadata=metadata,
            citations=citations,
        )