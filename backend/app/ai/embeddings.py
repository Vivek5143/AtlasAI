"""Sentence-transformer embedding services for AtlasAI."""

from __future__ import annotations

from functools import lru_cache
import logging
from time import perf_counter

from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer

from app.ai import EmbeddingServiceError
from app.config.settings import settings


LOGGER = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _load_sentence_transformer(model_name: str) -> SentenceTransformer:
    """Load and cache a sentence-transformer model once per process.

    Args:
        model_name: Hugging Face model name.

    Returns:
        SentenceTransformer: Loaded sentence-transformer model.

    Raises:
        EmbeddingServiceError: If the model cannot be loaded.
    """

    started_at = perf_counter()
    try:
        model = SentenceTransformer(model_name)
    except Exception as exc:  # pragma: no cover - depends on local model env
        raise EmbeddingServiceError(
            f"Failed to load embedding model '{model_name}'."
        ) from exc

    LOGGER.info(
        "Loaded embedding model '%s' in %.3f seconds.",
        model_name,
        perf_counter() - started_at,
    )
    return model


class AtlasAIEmbeddings(Embeddings):
    """Reusable embedding service backed by sentence-transformers."""

    def __init__(
        self,
        model_name: str | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize the embedding service.

        Args:
            model_name: Optional embedding model override.
            logger: Optional logger instance.
        """

        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._model = _load_sentence_transformer(self.model_name)

    def _encode(self, texts: list[str], prompt_name: str) -> list[list[float]]:
        """Encode a list of texts into vector embeddings.

        Args:
            texts: Source texts to embed.
            prompt_name: Either ``query`` or ``document`` for logging.

        Returns:
            list[list[float]]: Embedding vectors.

        Raises:
            EmbeddingServiceError: If encoding fails.
        """

        started_at = perf_counter()
        try:
            prepared_texts = [
                f"{'query' if prompt_name == 'query' else 'passage'}: {text}"
                for text in texts
            ]
            embeddings = self._model.encode(
                prepared_texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
        except Exception as exc:  # pragma: no cover - external model runtime
            raise EmbeddingServiceError(
                f"Failed to encode {prompt_name} text."
            ) from exc

        duration = perf_counter() - started_at
        self.logger.info(
            "Generated %s embedding(s) for %s in %.3f seconds.",
            len(texts),
            prompt_name,
            duration,
        )
        return embeddings.tolist()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed documents for vector indexing.

        Args:
            texts: Documents to embed.

        Returns:
            list[list[float]]: Document embeddings.
        """

        return self._encode(texts=texts, prompt_name="document")

    def embed_query(self, text: str) -> list[float]:
        """Embed a query string for semantic retrieval.

        Args:
            text: Query string to embed.

        Returns:
            list[float]: Query embedding.
        """

        return self._encode(texts=[text], prompt_name="query")[0]
