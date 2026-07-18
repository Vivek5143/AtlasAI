"""Database-to-Chroma ingestion pipeline for AtlasAI."""

from __future__ import annotations

from collections.abc import Iterable
import logging
from time import perf_counter
from typing import Any
from uuid import UUID

from langchain_core.documents import Document
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.ai import IndexingError
from app.ai.chunking import DocumentChunkingService
from app.ai.vector_store import ChromaVectorStoreService
from app.models.company import Company
from app.models.company_sector import CompanySector
from app.models.news_article import NewsArticle
from app.models.problem import Problem
from app.models.problem_company_mapping import ProblemCompanyMapping
from app.models.sector import Sector


class PostgresVectorIngestionService:
    """Index PostgreSQL records into the AtlasAI ChromaDB collection."""

    def __init__(
        self,
        session: Session,
        vector_store: ChromaVectorStoreService | None = None,
        chunker: DocumentChunkingService | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize the ingestion service.

        Args:
            session: Active SQLAlchemy session.
            vector_store: Optional vector store override.
            chunker: Optional chunking service override.
            logger: Optional logger instance.
        """

        self.session = session
        self.vector_store = vector_store or ChromaVectorStoreService()
        self.chunker = chunker or DocumentChunkingService()
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @staticmethod
    def _isoformat(value: Any) -> str | None:
        """Convert supported values to ISO timestamps.

        Args:
            value: Value to normalize.

        Returns:
            str | None: ISO string when available.
        """

        if value is None:
            return None
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value)

    @staticmethod
    def _serialize_id(value: Any) -> str | None:
        """Serialize identifiers into strings.

        Args:
            value: Identifier value.

        Returns:
            str | None: Serialized ID string.
        """

        return str(value) if value is not None else None

    @staticmethod
    def _compact_lines(lines: Iterable[str | None]) -> str:
        """Join non-empty text lines into a single page content string.

        Args:
            lines: Candidate lines for the page content.

        Returns:
            str: Compact multiline string.
        """

        return "\n".join(line for line in lines if line)

    def _base_metadata(
        self,
        *,
        entity_id: Any,
        entity_type: str,
        title: str,
        created_at: Any,
        source: str,
        company_id: Any = None,
        problem_id: Any = None,
        news_id: Any = None,
        sector_id: Any = None,
    ) -> dict[str, Any]:
        """Build the common metadata payload for indexed documents."""

        return {
            "id": self._serialize_id(entity_id),
            "entity_type": entity_type,
            "title": title,
            "created_at": self._isoformat(created_at),
            "company_id": self._serialize_id(company_id),
            "problem_id": self._serialize_id(problem_id),
            "news_id": self._serialize_id(news_id),
            "sector_id": self._serialize_id(sector_id),
            "source": source,
        }

    def _build_company_documents(self, companies: list[Company]) -> list[Document]:
        """Convert company records into LangChain documents."""

        documents: list[Document] = []
        for company in companies:
            sector_names = sorted(
                company_sector.sector.name
                for company_sector in company.company_sectors
                if company_sector.sector is not None
            )
            problem_names = sorted(
                mapping.problem.name
                for mapping in company.problem_mappings
                if mapping.problem is not None
            )

            page_content = self._compact_lines(
                [
                    f"Company: {company.vendor_name}",
                    f"Country: {company.country}" if company.country else None,
                    f"Website: {company.website}" if company.website else None,
                    f"Company Type: {company.company_type}" if company.company_type else None,
                    f"AI Category: {company.ai_category}" if company.ai_category else None,
                    f"Funding: {company.funding}" if company.funding else None,
                    (
                        f"Estimated Revenue: {company.estimated_revenue}"
                        if company.estimated_revenue
                        else None
                    ),
                    f"Maturity: {company.maturity}" if company.maturity else None,
                    (
                        f"Deployment Evidence: {company.deployment_evidence}"
                        if company.deployment_evidence
                        else None
                    ),
                    (
                        f"Sectors: {', '.join(sector_names)}"
                        if sector_names
                        else None
                    ),
                    (
                        f"Problems Solved: {', '.join(problem_names)}"
                        if problem_names
                        else None
                    ),
                ]
            )

            documents.append(
                Document(
                    page_content=page_content,
                    metadata=self._base_metadata(
                        entity_id=company.id,
                        entity_type="company",
                        title=company.vendor_name,
                        created_at=company.created_at,
                        company_id=company.id,
                        source="postgresql.companies",
                    ),
                )
            )

        return documents

    def _build_problem_documents(self, problems: list[Problem]) -> list[Document]:
        """Convert problem records into LangChain documents."""

        documents: list[Document] = []
        for problem in problems:
            mapped_companies = sorted(
                mapping.company.vendor_name
                for mapping in problem.company_mappings
                if mapping.company is not None
            )

            page_content = self._compact_lines(
                [
                    f"Problem: {problem.name}",
                    (
                        f"External Problem ID: {problem.external_problem_id}"
                        if problem.external_problem_id
                        else None
                    ),
                    f"Category: {problem.category}" if problem.category else None,
                    (
                        f"Problem Type: {problem.problem_type}"
                        if problem.problem_type
                        else None
                    ),
                    f"VC Stage: {problem.vc_stage}" if problem.vc_stage else None,
                    f"Severity: {problem.severity}" if problem.severity else None,
                    (
                        f"Financial Impact: {problem.financial_impact}"
                        if problem.financial_impact
                        else None
                    ),
                    (
                        f"Regulatory Trigger: {problem.regulatory_trigger}"
                        if problem.regulatory_trigger
                        else None
                    ),
                    f"AI Solution: {problem.ai_solution}" if problem.ai_solution else None,
                    (
                        f"Related Companies: {', '.join(mapped_companies)}"
                        if mapped_companies
                        else None
                    ),
                ]
            )

            documents.append(
                Document(
                    page_content=page_content,
                    metadata=self._base_metadata(
                        entity_id=problem.id,
                        entity_type="problem",
                        title=problem.name,
                        created_at=problem.created_at,
                        problem_id=problem.id,
                        source="postgresql.problems",
                    ),
                )
            )

        return documents

    def _build_news_documents(self, news_articles: list[NewsArticle]) -> list[Document]:
        """Convert news article records into LangChain documents."""

        documents: list[Document] = []
        for article in news_articles:
            company_name = article.company.vendor_name if article.company is not None else None
            page_content = self._compact_lines(
                [
                    f"News Article: {article.title}",
                    f"Company: {company_name}" if company_name else None,
                    f"URL: {article.url}",
                    f"Published At: {self._isoformat(article.published_at)}",
                ]
            )

            documents.append(
                Document(
                    page_content=page_content,
                    metadata=self._base_metadata(
                        entity_id=article.id,
                        entity_type="news",
                        title=article.title,
                        created_at=article.created_at,
                        company_id=article.company_id,
                        news_id=article.id,
                        source="postgresql.news_articles",
                    ),
                )
            )

        return documents

    def _build_sector_documents(self, sectors: list[Sector]) -> list[Document]:
        """Convert sector records into LangChain documents."""

        documents: list[Document] = []
        for sector in sectors:
            company_names = sorted(
                company_sector.company.vendor_name
                for company_sector in sector.company_sectors
                if company_sector.company is not None
            )

            page_content = self._compact_lines(
                [
                    f"Sector: {sector.name}",
                    (
                        f"Companies: {', '.join(company_names)}"
                        if company_names
                        else None
                    ),
                ]
            )

            documents.append(
                Document(
                    page_content=page_content,
                    metadata=self._base_metadata(
                        entity_id=sector.id,
                        entity_type="sector",
                        title=sector.name,
                        created_at=sector.created_at,
                        sector_id=sector.id,
                        source="postgresql.sectors",
                    ),
                )
            )

        return documents

    def _chunk_with_ids(self, documents: list[Document]) -> tuple[list[Document], list[str]]:
        """Chunk documents and build deterministic vector IDs.

        Args:
            documents: Base documents to chunk.

        Returns:
            tuple[list[Document], list[str]]: Chunked documents and vector IDs.
        """

        chunked_documents = self.chunker.chunk_documents(documents)
        vector_ids: list[str] = []

        for index, document in enumerate(chunked_documents):
            document.metadata["chunk_index"] = index
            entity_type = document.metadata["entity_type"]
            entity_id = document.metadata["id"]
            vector_ids.append(f"{entity_type}:{entity_id}:{index}")

        return chunked_documents, vector_ids

    def _index_documents(self, documents: list[Document]) -> int:
        """Chunk and upsert documents into ChromaDB.

        Args:
            documents: Base LangChain documents.

        Returns:
            int: Number of indexed chunks.
        """

        if not documents:
            return 0

        chunked_documents, vector_ids = self._chunk_with_ids(documents)
        self.vector_store.update_documents(chunked_documents, vector_ids)
        return len(chunked_documents)

    def index_companies(self) -> int:
        """Index all company records from PostgreSQL.

        Returns:
            int: Number of indexed company chunks.
        """

        started_at = perf_counter()
        try:
            companies = list(
                self.session.execute(
                    select(Company)
                    .options(
                        selectinload(Company.company_sectors).selectinload(CompanySector.sector),
                        selectinload(Company.problem_mappings).selectinload(ProblemCompanyMapping.problem),
                    )
                    .order_by(Company.vendor_name.asc())
                ).scalars().all()
            )
            indexed_count = self._index_documents(self._build_company_documents(companies))
        except Exception as exc:  # pragma: no cover - depends on DB runtime
            raise IndexingError("Failed to index companies from PostgreSQL.") from exc

        self.logger.info(
            "Indexed %s company chunk(s) in %.3f seconds.",
            indexed_count,
            perf_counter() - started_at,
        )
        return indexed_count

    def index_company_by_id(self, company_id: UUID) -> int:
        """Index one company record from PostgreSQL.

        Args:
            company_id: Company identifier to index.

        Returns:
            int: Number of indexed company chunks.
        """

        started_at = perf_counter()
        try:
            companies = list(
                self.session.execute(
                    select(Company)
                    .options(
                        selectinload(Company.company_sectors).selectinload(CompanySector.sector),
                        selectinload(Company.problem_mappings).selectinload(ProblemCompanyMapping.problem),
                    )
                    .where(Company.id == company_id)
                ).scalars().all()
            )
            indexed_count = self._index_documents(self._build_company_documents(companies))
        except Exception as exc:  # pragma: no cover - depends on DB/Chroma runtime
            raise IndexingError("Failed to index selected company from PostgreSQL.") from exc

        self.logger.info(
            "Indexed %s selected company chunk(s) in %.3f seconds.",
            indexed_count,
            perf_counter() - started_at,
        )
        return indexed_count

    def index_news(self) -> int:
        """Index all news articles from PostgreSQL.

        Returns:
            int: Number of indexed news chunks.
        """

        started_at = perf_counter()
        try:
            news_articles = list(
                self.session.execute(
                    select(NewsArticle)
                    .options(selectinload(NewsArticle.company))
                    .order_by(NewsArticle.published_at.desc())
                ).scalars().all()
            )
            indexed_count = self._index_documents(self._build_news_documents(news_articles))
        except Exception as exc:  # pragma: no cover - depends on DB runtime
            raise IndexingError("Failed to index news articles from PostgreSQL.") from exc

        self.logger.info(
            "Indexed %s news chunk(s) in %.3f seconds.",
            indexed_count,
            perf_counter() - started_at,
        )
        return indexed_count

    def index_news_by_ids(self, news_ids: list[UUID]) -> int:
        """Index only selected news articles from PostgreSQL.

        Args:
            news_ids: News article identifiers to index.

        Returns:
            int: Number of indexed news chunks.
        """

        if not news_ids:
            return 0

        started_at = perf_counter()
        try:
            news_articles = list(
                self.session.execute(
                    select(NewsArticle)
                    .options(selectinload(NewsArticle.company))
                    .where(NewsArticle.id.in_(news_ids))
                    .order_by(NewsArticle.published_at.desc())
                ).scalars().all()
            )
            indexed_count = self._index_documents(self._build_news_documents(news_articles))
        except Exception as exc:  # pragma: no cover - depends on DB runtime
            raise IndexingError("Failed to index selected news articles from PostgreSQL.") from exc

        self.logger.info(
            "Indexed %s selected news chunk(s) in %.3f seconds.",
            indexed_count,
            perf_counter() - started_at,
        )
        return indexed_count

    def index_problems(self) -> int:
        """Index all problem records from PostgreSQL.

        Returns:
            int: Number of indexed problem chunks.
        """

        started_at = perf_counter()
        try:
            problems = list(
                self.session.execute(
                    select(Problem)
                    .options(
                        selectinload(Problem.company_mappings).selectinload(ProblemCompanyMapping.company),
                    )
                    .order_by(Problem.name.asc())
                ).scalars().all()
            )
            indexed_count = self._index_documents(self._build_problem_documents(problems))
        except Exception as exc:  # pragma: no cover - depends on DB runtime
            raise IndexingError("Failed to index problems from PostgreSQL.") from exc

        self.logger.info(
            "Indexed %s problem chunk(s) in %.3f seconds.",
            indexed_count,
            perf_counter() - started_at,
        )
        return indexed_count

    def index_sectors(self) -> int:
        """Index all sector records from PostgreSQL.

        Returns:
            int: Number of indexed sector chunks.
        """

        started_at = perf_counter()
        try:
            sectors = list(
                self.session.execute(
                    select(Sector)
                    .options(
                        selectinload(Sector.company_sectors).selectinload(CompanySector.company),
                    )
                    .order_by(Sector.name.asc())
                ).scalars().all()
            )
            indexed_count = self._index_documents(self._build_sector_documents(sectors))
        except Exception as exc:  # pragma: no cover - depends on DB runtime
            raise IndexingError("Failed to index sectors from PostgreSQL.") from exc

        self.logger.info(
            "Indexed %s sector chunk(s) in %.3f seconds.",
            indexed_count,
            perf_counter() - started_at,
        )
        return indexed_count

    def index_all(self) -> dict[str, int]:
        """Index all supported PostgreSQL entities into ChromaDB.

        Returns:
            dict[str, int]: Chunk counts per entity type.
        """

        started_at = perf_counter()
        summary = {
            "companies": self.index_companies(),
            "news": self.index_news(),
            "problems": self.index_problems(),
            "sectors": self.index_sectors(),
        }
        summary["total"] = sum(summary.values())
        self.logger.info(
            "Indexed all entity types into ChromaDB in %.3f seconds: %s",
            perf_counter() - started_at,
            summary,
        )
        return summary

    def reindex_all(self) -> dict[str, int]:
        """Clear the vector store and rebuild the full index.

        Returns:
            dict[str, int]: Reindexing summary.
        """

        started_at = perf_counter()
        self.vector_store.clear_collection()
        summary = self.index_all()
        self.logger.info(
            "Reindexed the entire ChromaDB collection in %.3f seconds.",
            perf_counter() - started_at,
        )
        return summary
