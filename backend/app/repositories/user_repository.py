"""Repository pattern for User operations."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security.security import hash_password
from app.models.user import User


class UserRepository:
    """Repository for user persistence and query logic."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, user_id: UUID) -> User | None:
        """Fetch user by ID."""

        return self.session.execute(select(User).where(User.id == user_id)).scalars().first()

    def get_by_email(self, email: str) -> User | None:
        """Fetch user by normalized email address."""

        normalized = email.strip().lower()
        return self.session.execute(
            select(User).where(func.lower(User.email) == normalized)
        ).scalars().first()

    def get_by_username(self, username: str) -> User | None:
        """Fetch user by normalized username."""

        normalized = username.strip().lower()
        return self.session.execute(
            select(User).where(func.lower(User.username) == normalized)
        ).scalars().first()

    def count_admins(self) -> int:
        """Count users with admin role."""

        return self.session.execute(
            select(func.count(User.id)).where(User.role == "admin")
        ).scalar() or 0

    def create_user(
        self,
        *,
        username: str,
        email: str,
        password: str,
        role: str = "user",
    ) -> User:
        """Create and persist a user with securely hashed password."""

        user = User(
            username=username.strip(),
            email=email.strip().lower(),
            hashed_password=hash_password(password),
            role=role,
        )
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
