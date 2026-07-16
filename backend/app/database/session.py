"""Database engine and session management for the application.

This module exposes the shared SQLAlchemy engine, a configured session factory,
and the FastAPI dependency used to provide request-scoped database sessions.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import settings


engine: Engine = create_engine(
    settings.DATABASE_URL,
    future=True,
)
"""Shared synchronous SQLAlchemy engine for database access."""


SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    future=True,
    class_=Session,
)
"""Factory for creating synchronous SQLAlchemy session instances."""


def get_db() -> Generator[Session, None, None]:
    """Yield a database session for the current request lifecycle.

    Yields:
        Session: An active SQLAlchemy session bound to the application engine.

    The session is always closed after use, even if request handling raises
    an exception.
    """

    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
