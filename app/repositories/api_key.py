from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import UserApiKey


class ApiKeyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_active_by_prefix(self, prefix: str) -> UserApiKey | None:
        result = await self.session.execute(
            select(UserApiKey).where(
                UserApiKey.key_prefix == prefix,
                UserApiKey.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def revoke_for_user(self, user_id: UUID) -> None:
        now = datetime.now(UTC)
        await self.session.execute(
            update(UserApiKey)
            .where(UserApiKey.user_id == user_id, UserApiKey.is_active.is_(True))
            .values(is_active=False, revoked_at=now)
        )

    async def revoke_for_session(self, session_id: UUID) -> None:
        now = datetime.now(UTC)
        await self.session.execute(
            update(UserApiKey)
            .where(UserApiKey.session_id == session_id, UserApiKey.is_active.is_(True))
            .values(is_active=False, revoked_at=now)
        )

    async def add(self, api_key: UserApiKey) -> UserApiKey:
        self.session.add(api_key)
        await self.session.flush()
        return api_key
