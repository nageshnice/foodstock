from collections.abc import AsyncIterator, Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.permissions import Permission, has_permission
from app.core.security import decode_access_token
from app.database.session import get_db_session
from app.models.domain import User
from app.repositories.user import UserRepository
from app.services.api_keys import ApiKeyService

SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> User:
    if x_api_key:
        record = await ApiKeyService(session).authenticate(x_api_key.strip())
        if not record:
            raise AppException("Invalid API key", status_code=401, code="invalid_api_key")
        user = await UserRepository(session).get_by_id(record.user_id)
        if not user or not user.is_active:
            raise AppException("Account is unavailable", status_code=401, code="account_unavailable")
        await session.commit()
        return user

    if credentials is None:
        raise AppException("Authentication required", status_code=401, code="not_authenticated")
    claims = decode_access_token(credentials.credentials)
    try:
        user_id = UUID(claims["sub"])
    except (KeyError, ValueError) as exc:
        raise AppException(
            "Invalid access token", status_code=401, code="invalid_access_token"
        ) from exc

    user = await UserRepository(session).get_by_id(user_id)
    if not user or not user.is_active:
        raise AppException("Account is unavailable", status_code=401, code="account_unavailable")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_permission(permission: Permission) -> Callable[..., AsyncIterator[User]]:
    async def permission_dependency(user: CurrentUser) -> AsyncIterator[User]:
        if not has_permission(user.role, permission):
            raise AppException("Permission denied", status_code=403, code="permission_denied")
        yield user

    return permission_dependency
