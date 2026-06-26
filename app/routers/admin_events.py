import asyncio
from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.core.dependencies import SessionDep
from app.core.events import admin_event_bus
from app.core.exceptions import AppException
from app.core.permissions import Permission, has_permission
from app.core.security import decode_access_token
from app.models.domain import User
from app.repositories.user import UserRepository

router = APIRouter(prefix="/admin", tags=["Admin Events"])


async def _authorized_admin(token: str, session: SessionDep) -> User:
    claims = decode_access_token(token)
    try:
        user_id = UUID(claims["sub"])
    except (KeyError, ValueError) as exc:
        raise AppException(
            "Invalid access token", status_code=401, code="invalid_access_token"
        ) from exc
    user = await UserRepository(session).get_by_id(user_id)
    if not user or not user.is_active:
        raise AppException("Account is unavailable", status_code=401, code="account_unavailable")
    if not has_permission(user.role, Permission.VIEW_ADMIN):
        raise AppException("Permission denied", status_code=403, code="permission_denied")
    return user


@router.get("/events/stream")
async def admin_event_stream(
    session: SessionDep,
    token: str = Query(..., min_length=10),
) -> StreamingResponse:
    await _authorized_admin(token, session)

    async def event_generator() -> AsyncIterator[str]:
        yield "event: connected\ndata: {}\n\n"
        heartbeat = 0
        async for payload in admin_event_bus.subscribe():
            yield f"event: update\ndata: {payload}\n\n"
            heartbeat += 1
            if heartbeat % 5 == 0:
                yield ": heartbeat\n\n"
                await asyncio.sleep(0)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
