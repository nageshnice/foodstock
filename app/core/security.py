from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import get_settings
from app.core.exceptions import AppException

password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Create a secure, salted password hash."""

    return password_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Safely compare a plain password with its stored hash."""

    return password_hasher.verify(password, hashed_password)


def create_access_token(subject: str, extra_claims: dict[str, Any] | None = None) -> str:
    """Create a signed access token for a subject identifier."""

    settings = get_settings()
    now = datetime.now(UTC)
    payload: dict[str, Any] = dict(extra_claims or {})
    payload.update(
        {
            "sub": subject,
            "iat": now,
            "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
            "type": "access",
        }
    )

    return jwt.encode(
        payload,
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """Validate an access token and return its claims."""

    settings = get_settings()
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
        )
    except ExpiredSignatureError as exc:
        raise AppException(
            "Access token expired. Please log in again.",
            status_code=401,
            code="access_token_expired",
        ) from exc
    except InvalidTokenError as exc:
        raise AppException(
            "Invalid access token",
            status_code=401,
            code="invalid_access_token",
        ) from exc

    if payload.get("type") != "access" or not payload.get("sub"):
        raise AppException(
            "Invalid access token",
            status_code=401,
            code="invalid_access_token",
        )
    return payload
