"""FastAPI dependency providers for v1 endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security.security import decode_access_token
from app.database.session import get_db
from app.models.user import User
from app.repositories.company_discovery_repository import CompanyDiscoveryRepository
from app.repositories.company_repository import CompanyRepository
from app.repositories.news_repository import NewsRepository
from app.repositories.problem_repository import ProblemRepository
from app.repositories.sector_repository import SectorRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.company_discovery_service import CompanyDiscoveryService
from app.services.company_service import CompanyService
from app.services.news_service import NewsService
from app.services.news_sync_service import NewsSyncService
from app.services.problem_service import ProblemService
from app.services.sector_service import SectorService

security_scheme = HTTPBearer(auto_error=False)


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Provide an AuthService backed by the request DB session."""

    auth_service = AuthService(session=db, repository=UserRepository(db))
    auth_service.seed_initial_admin()
    return auth_service


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Authenticate Bearer token and return current User instance."""

    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    claims = decode_access_token(credentials.credentials)
    if not claims or "sub" not in claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = UUID(claims["sub"])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user subject in token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found or inactive.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Authorize user for admin-only actions."""

    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required to access Company Discovery management.",
        )
    return current_user


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


def get_ai_chat_service(db: Session = Depends(get_db)):
    """Provide the AtlasAI RAG chat service backed by the request DB session."""

    from app.ai.chat import AtlasAIRAGChatService

    return AtlasAIRAGChatService(session=db)
