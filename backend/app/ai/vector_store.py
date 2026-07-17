"""ChromaDB vector store integration for AtlasAI."""

from __future__ import annotations

import logging
from pathlib import Path
from time import perf_counter

from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.ai import EmptyVectorStoreError, VectorStoreError
from app.ai.embeddings import AtlasAIEmbeddings
from app.config.settings import settings


class ChromaVectorStoreService:
    """Reusable ChromaDB wrapper for persistent vector operations."""

    def __init__(
        self,
        embeddings: AtlasAIEmbeddings | None = None,
        collection_name: str = "atlasai_knowledge_base",
        persist_directory: str | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize the ChromaDB vector store service.

        Args:
            embeddings: Optional embedding service override.
            collection_name: Chroma collection name.
            persist_directory: Optional persistence path override.
            logger: Optional logger instance.
        """

        self.embeddings = embeddings or AtlasAIEmbeddings()
        self.collection_name = collection_name
        self.persist_directory = persist_directory or settings.CHROMA_DB_PATH
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._vector_store: Chroma | None = None

    def initialize(self) -> Chroma:
        """Initialize and return the persistent Chroma collection.

        Returns:
            Chroma: Initialized Chroma vector store.

        Raises:
            VectorStoreError: If initialization fails.
        """

        if self._vector_store is not None:
            return self._vector_store

        started_at = perf_counter()
        try:
            Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
            self._vector_store = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory,
            )
        except Exception as exc:  # pragma: no cover - external storage runtime
            raise VectorStoreError("Failed to initialize ChromaDB.") from exc

        self.logger.info(
            "Initialized ChromaDB collection '%s' at '%s' in %.3f seconds.",
            self.collection_name,
            self.persist_directory,
            perf_counter() - started_at,
        )
        return self._vector_store

    def get_collection(self) -> Chroma:
        """Return the initialized Chroma collection.

        Returns:
            Chroma: Active vector store instance.
        """

        return self.initialize()

    def document_count(self) -> int:
        """Return the number of indexed vectors in the collection.

        Returns:
            int: Indexed vector count.
        """

        try:
            return int(self.get_collection()._collection.count())
        except Exception as exc:  # pragma: no cover - external storage runtime
            raise VectorStoreError("Failed to count ChromaDB documents.") from exc

    def add_documents(self, documents: list[Document], ids: list[str]) -> list[str]:
        """Add LangChain documents to the collection.

        Args:
            documents: Documents to add.
            ids: Stable vector document IDs.

        Returns:
            list[str]: Persisted document IDs.
        """

        if not documents:
            return []

        started_at = perf_counter()
        try:
            self.get_collection().add_documents(documents=documents, ids=ids)
        except Exception as exc:  # pragma: no cover - external storage runtime
            raise VectorStoreError("Failed to add documents to ChromaDB.") from exc

        self.logger.info(
            "Indexed %s document chunk(s) in %.3f seconds.",
            len(documents),
            perf_counter() - started_at,
        )
        return ids

    def update_documents(self, documents: list[Document], ids: list[str]) -> list[str]:
        """Upsert documents in the collection using stable IDs.

        Args:
            documents: Documents to upsert.
            ids: Stable vector document IDs.

        Returns:
            list[str]: Updated document IDs.
        """

        if not documents:
            return []

        started_at = perf_counter()
        try:
            self.delete_documents(ids=ids, raise_if_missing=False)
            self.get_collection().add_documents(documents=documents, ids=ids)
        except Exception as exc:  # pragma: no cover - external storage runtime
            raise VectorStoreError("Failed to update documents in ChromaDB.") from exc

        self.logger.info(
            "Upserted %s document chunk(s) in %.3f seconds.",
            len(documents),
            perf_counter() - started_at,
        )
        return ids

    def delete_documents(
        self,
        ids: list[str],
        raise_if_missing: bool = False,
    ) -> None:
        """Delete documents by vector IDs.

        Args:
            ids: Vector IDs to delete.
            raise_if_missing: Whether to raise when deletion fails.
        """

        if not ids:
            return

        try:
            self.get_collection().delete(ids=ids)
        except Exception as exc:  # pragma: no cover - external storage runtime
            if raise_if_missing:
                raise VectorStoreError("Failed to delete ChromaDB documents.") from exc
            self.logger.debug("Ignored ChromaDB delete failure: %s", exc)

    def search(self, query: str, top_k: int = 4) -> list[tuple[Document, float]]:
        """Perform semantic similarity search.

        Args:
            query: User query string.
            top_k: Maximum number of chunks to return.

        Returns:
            list[tuple[Document, float]]: Retrieved documents and relevance scores.

        Raises:
            EmptyVectorStoreError: If the collection is empty.
            VectorStoreError: If search fails.
        """

        if self.document_count() == 0:
            raise EmptyVectorStoreError("The ChromaDB collection is empty.")

        started_at = perf_counter()
        try:
            results = self.get_collection().similarity_search_with_relevance_scores(
                query=query,
                k=top_k,
            )
        except Exception as exc:  # pragma: no cover - external storage runtime
            raise VectorStoreError("Failed to search ChromaDB.") from exc

        self.logger.info(
            "Semantic search returned %s document(s) in %.3f seconds.",
            len(results),
            perf_counter() - started_at,
        )
        return results

    def clear_collection(self) -> None:
        """Delete all indexed documents from the collection."""

        try:
            vector_store = self.get_collection()
            payload = vector_store.get(include=[])
            ids = payload.get("ids", [])
            if ids:
                vector_store.delete(ids=ids)
        except Exception as exc:  # pragma: no cover - external storage runtime
            raise VectorStoreError("Failed to clear the ChromaDB collection.") from exc

        self.logger.info("Cleared ChromaDB collection '%s'.", self.collection_name)
