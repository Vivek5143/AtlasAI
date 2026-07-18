"""FastAPI dependency providers for v1 endpoints."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session


from app.database.session import get_db
from app.repositories.news_repository import NewsRepository
from app.repositories.company_discovery_repository import CompanyDiscoveryRepository
from app.repositories.company_repository import CompanyRepository
from app.repositories.sector_repository import SectorRepository
from app.repositories.problem_repository import ProblemRepository
from app.services.company_service import CompanyService
from app.services.sector_service import SectorService
from app.services.problem_service import ProblemService
from app.services.news_service import NewsService
from app.services.news_sync_service import NewsSyncService
from app.services.company_discovery_service import CompanyDiscoveryService
from app.ai.chat import AtlasAIRAGChatService


def get_company_service(db: Session = Depends(get_db)) -> CompanyService:
    """Provide a CompanyService backed by the request-scoped DB session."""

    return CompanyService(CompanyRepository(db))



def get_sector_service(db: Session = Depends(get_db)) -> SectorService:

    """Provide a SectorService backed by the request-scoped DB session."""

    return SectorService(SectorRepository(db))


def get_problem_service(db: Session = Depends(get_db)) -> ProblemService:

    """Provide a ProblemService backed by the request-scoped DB session."""

    return ProblemService(ProblemRepository(db))


def get_news_service(db: Session = Depends(get_db)) -> NewsService:

    """Provide a NewsService backed by the request-scoped DB session."""

    return NewsService(session=db, repository=NewsRepository(db))


def get_news_sync_service(db: Session = Depends(get_db)) -> NewsSyncService:
    """Provide a NewsSyncService backed by the request-scoped DB session."""

    return NewsSyncService(session=db, news_repository=NewsRepository(db))


def get_company_discovery_service(db: Session = Depends(get_db)) -> CompanyDiscoveryService:
    """Provide the CompanyDiscoveryService backed by the request DB session."""

    return CompanyDiscoveryService(
        session=db,
        repository=CompanyDiscoveryRepository(db),
        company_service=CompanyService(CompanyRepository(db)),
    )


def get_ai_chat_service(db: Session = Depends(get_db)) -> AtlasAIRAGChatService:
    """Provide the AtlasAI RAG chat service backed by the request DB session."""

    return AtlasAIRAGChatService(session=db)
