"""Security helpers for password hashing and signed access tokens."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any

from app.config.settings import settings

ALGORITHM = "HS256"
DEFAULT_EXPIRE_SECONDS = 86400 * 7  # 7 days


def hash_password(password: str) -> str:
    """Hash a plaintext password using PBKDF2 with SHA-256 and a random salt."""

    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"{salt.hex()}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored PBKDF2 hash."""

    if not plain_password or not hashed_password or "$" not in hashed_password:
        return False

    try:
        salt_hex, key_hex = hashed_password.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(key_hex)
        actual_key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 100_000)
        return hmac.compare_digest(expected_key, actual_key)
    except (ValueError, TypeError):
        return False


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64decode(data: str) -> bytes:
    padding = 4 - (len(data) % 4)
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data.encode("utf-8"))


def create_access_token(payload: dict[str, Any], expires_in: int = DEFAULT_EXPIRE_SECONDS) -> str:
    """Create a signed HMAC-SHA256 access token containing claims."""

    header = {"alg": ALGORITHM, "typ": "JWT"}
    claims = {**payload, "exp": int(time.time()) + expires_in}

    header_b64 = _b64encode(json.dumps(header).encode("utf-8"))
    claims_b64 = _b64encode(json.dumps(claims).encode("utf-8"))
    signing_input = f"{header_b64}.{claims_b64}".encode("utf-8")

    secret = settings.SECRET_KEY.encode("utf-8") or b"default-secret-key"
    signature = hmac.new(secret, signing_input, hashlib.sha256).digest()
    sig_b64 = _b64encode(signature)

    return f"{header_b64}.{claims_b64}.{sig_b64}"


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode and verify an HMAC-SHA256 signed access token."""

    parts = token.split(".")
    if len(parts) != 3:
        return None

    header_b64, claims_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{claims_b64}".encode("utf-8")
    secret = settings.SECRET_KEY.encode("utf-8") or b"default-secret-key"
    expected_signature = hmac.new(secret, signing_input, hashlib.sha256).digest()

    try:
        actual_signature = _b64decode(sig_b64)
        if not hmac.compare_digest(expected_signature, actual_signature):
            return None

        claims = json.loads(_b64decode(claims_b64).decode("utf-8"))
        if not isinstance(claims, dict):
            return None

        exp = claims.get("exp")
        if isinstance(exp, (int, float)) and time.time() > exp:
            return None

        return claims
    except Exception:
        return None
