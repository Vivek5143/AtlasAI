"""Unit tests for password hashing, token issuance, auth service, and admin authorization."""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ["DEBUG"] = "true"

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1.dependencies import get_current_admin_user
from app.config.settings import settings
from app.core.security.security import create_access_token, decode_access_token, hash_password, verify_password
from app.database.base import Base
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService


class SecurityUtilitiesTests(unittest.TestCase):
    """Password hashing and JWT token tests."""

    def test_password_hashing_and_verification(self) -> None:
        password = "SecurePassword123!"
        hashed = hash_password(password)

        self.assertNotEqual(password, hashed)
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password("WrongPassword!", hashed))

    def test_token_creation_and_decoding(self) -> None:
        payload = {"sub": "12345", "role": "admin", "username": "admin_user"}
        token = create_access_token(payload)

        decoded = decode_access_token(token)

        self.assertIsNotNone(decoded)
        self.assertEqual(decoded["sub"], "12345")
        self.assertEqual(decoded["role"], "admin")
        self.assertEqual(decoded["username"], "admin_user")

    def test_invalid_token_returns_none(self) -> None:
        self.assertIsNone(decode_access_token("invalid.token.structure"))


class AuthServiceAndAuthorizationTests(unittest.TestCase):
    """Auth service and authorization dependency tests."""

    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite://",
            future=True,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        testing_session = sessionmaker(bind=self.engine, class_=Session, future=True)
        self.session = testing_session()

    def tearDown(self) -> None:
        self.session.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_admin_seeding_creates_admin_user_from_config(self) -> None:
        settings.INITIAL_ADMIN_EMAIL = "admin_test@atlasai.com"
        settings.INITIAL_ADMIN_PASSWORD = "AdminPassword123!"
        settings.INITIAL_ADMIN_USERNAME = "testadmin"

        auth_service = AuthService(self.session)
        admin = auth_service.seed_initial_admin()

        self.assertIsNotNone(admin)
        self.assertEqual(admin.username, "testadmin")
        self.assertEqual(admin.email, "admin_test@atlasai.com")
        self.assertEqual(admin.role, "admin")
        self.assertTrue(admin.is_admin)

    def test_authenticate_user_with_valid_and_invalid_credentials(self) -> None:
        repo = UserRepository(self.session)
        repo.create_user(username="johndoe", email="john@example.com", password="MyPassword123!", role="user")

        auth_service = AuthService(self.session, repository=repo)

        user = auth_service.authenticate_user("john@example.com", "MyPassword123!")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "johndoe")

        invalid_pass = auth_service.authenticate_user("john@example.com", "WrongPassword!")
        self.assertIsNone(invalid_pass)

    def test_non_admin_user_raises_403_in_admin_guard(self) -> None:
        normal_user = User(username="user1", email="u1@test.com", hashed_password="x", role="user")

        with self.assertRaises(HTTPException) as cm:
            get_current_admin_user(current_user=normal_user)

        self.assertEqual(cm.exception.status_code, 403)
        self.assertIn("Admin role required", cm.exception.detail)

    def test_admin_user_passes_admin_guard(self) -> None:
        admin_user = User(username="admin1", email="a1@test.com", hashed_password="x", role="admin")

        result = get_current_admin_user(current_user=admin_user)
        self.assertEqual(result.username, "admin1")


if __name__ == "__main__":
    unittest.main()
