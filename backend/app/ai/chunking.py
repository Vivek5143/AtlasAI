"""Text chunking services for AtlasAI RAG indexing."""

from __future__ import annotations

import logging
from time import perf_counter

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocumentChunkingService:
    """Chunk LangChain documents while preserving metadata."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize the chunking service.

        Args:
            chunk_size: Maximum chunk size.
            chunk_overlap: Overlap between adjacent chunks.
            logger: Optional logger instance.
        """

        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def chunk_documents(self, documents: list[Document]) -> list[Document]:
        """Split documents into chunks while retaining metadata.

        Args:
            documents: Documents to chunk.

        Returns:
            list[Document]: Chunked documents.
        """

        if not documents:
            return []

        started_at = perf_counter()
        chunked_documents = self.splitter.split_documents(documents)
        self.logger.info(
            "Chunked %s document(s) into %s chunk(s) in %.3f seconds.",
            len(documents),
            len(chunked_documents),
            perf_counter() - started_at,
        )
        return chunked_documents
