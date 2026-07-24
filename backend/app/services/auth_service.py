"""Authentication service and admin initialization."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.config.settings import settings
from app.core.security.security import create_access_token, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository


class AuthService:
    """Authentication workflow manager."""

    def __init__(
        self,
        session: Session,
        repository: UserRepository | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.session = session
        self.repository = repository or UserRepository(session)
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def seed_initial_admin(self) -> User | None:
        """Seed initial admin user from environment variables if no admin exists."""

        if self.repository.count_admins() > 0:
            return None

        email = settings.INITIAL_ADMIN_EMAIL.strip()
        password = settings.INITIAL_ADMIN_PASSWORD
        username = settings.INITIAL_ADMIN_USERNAME.strip() or "admin"

        if not email or not password:
            self.logger.info("No initial admin configured in environment variables.")
            return None

        existing = self.repository.get_by_email(email)
        if existing:
            if existing.role != "admin":
                existing.role = "admin"
                self.session.commit()
                self.session.refresh(existing)
            return existing

        admin_user = self.repository.create_user(
            username=username,
            email=email,
            password=password,
            role="admin",
        )
        self.logger.info(
            "Initial admin account created from environment configuration.",
            extra={"username": username, "email": email, "role": "admin"},
        )
        return admin_user

    def authenticate_user(self, username_or_email: str, password: str) -> User | None:
        """Authenticate user by email/username and password."""

        if not username_or_email or not password:
            return None

        user = self.repository.get_by_email(username_or_email)
        if not user:
            user = self.repository.get_by_username(username_or_email)

        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user

    def generate_auth_response(self, user: User) -> dict[str, Any]:
        """Generate access token and user metadata for API response."""

        payload = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role,
        }
        token = create_access_token(payload)

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "is_admin": user.is_admin,
            },
        }
