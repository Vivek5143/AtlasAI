"""Pydantic schemas for auth endpoints."""

from __future__ import annotations

from uuid import UUID
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Payload for user sign in."""

    username_or_email: str
    password: str


class UserResponse(BaseModel):
    """Safe user profile response."""

    id: UUID
    username: str
    email: EmailStr
    role: str
    is_admin: bool

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Authentication token response payload."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse
