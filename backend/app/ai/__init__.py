"""AtlasAI AI and RAG services."""

from dataclasses import dataclass
from typing import Any


class AIServiceError(Exception):
    """Base exception for AI module failures."""


class MissingConfigurationError(AIServiceError):
    """Raised when required AI configuration is missing."""


class EmbeddingServiceError(AIServiceError):
    """Raised when embedding generation fails."""


class VectorStoreError(AIServiceError):
    """Raised when ChromaDB operations fail."""


class RetrievalError(AIServiceError):
    """Raised when semantic retrieval fails."""


class IndexingError(AIServiceError):
    """Raised when database content cannot be indexed."""


class ChatGenerationError(AIServiceError):
    """Raised when the language model cannot generate a response."""


class EmptyVectorStoreError(AIServiceError):
    """Raised when the vector store has no indexed documents."""


@dataclass(slots=True, frozen=True)
class RetrievedChunk:
    """Represents a semantically retrieved chunk.

    Attributes:
        page_content: Retrieved chunk content.
        metadata: Associated metadata returned from ChromaDB.
        score: Relevance score for the chunk.
    """

    page_content: str
    metadata: dict[str, Any]
    score: float


__all__ = [
    "AIServiceError",
    "ChatGenerationError",
    "EmbeddingServiceError",
    "EmptyVectorStoreError",
    "IndexingError",
    "MissingConfigurationError",
    "RetrievedChunk",
    "RetrievalError",
    "VectorStoreError",
]
