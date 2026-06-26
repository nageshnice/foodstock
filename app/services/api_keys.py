import secrets
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.domain import User, UserApiKey, UserLoginSession
from app.repositories.api_key import ApiKeyRepository


def generate_api_key() -> str:
    return f"fsk_{secrets.token_urlsafe(32)}"


def hash_api_key(raw_key: str) -> str:
    return hash_password(raw_key)


def verify_api_key(raw_key: str, key_hash: str) -> bool:
    return verify_password(raw_key, key_hash)


class ApiKeyService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.keys = ApiKeyRepository(session)

    async def issue_for_login(
        self, user: User, login_session: UserLoginSession
    ) -> str:
        """Revoke old keys, create a fresh API key for this login session."""
        await self.keys.revoke_for_user(user.id)
        raw_key = generate_api_key()
        await self.keys.add(
            UserApiKey(
                user_id=user.id,
                session_id=login_session.id,
                key_prefix=raw_key[:16],
                key_hash=hash_api_key(raw_key),
            )
        )
        await self.session.flush()
        return raw_key

    async def authenticate(self, raw_key: str) -> UserApiKey | None:
        if len(raw_key) < 16:
            return None
        prefix = raw_key[:16]
        record = await self.keys.get_active_by_prefix(prefix)
        if not record or not verify_api_key(raw_key, record.key_hash):
            return None
        from datetime import UTC, datetime

        record.last_used_at = datetime.now(UTC)
        await self.session.flush()
        return record

    async def revoke_for_session(self, session_id: UUID) -> None:
        await self.keys.revoke_for_session(session_id)

    async def revoke_for_user(self, user_id: UUID) -> None:
        await self.keys.revoke_for_user(user_id)
