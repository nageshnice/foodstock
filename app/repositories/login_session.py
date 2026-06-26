from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import UserLoginSession


class LoginSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, session_id: UUID) -> UserLoginSession | None:
        result = await self.session.execute(
            select(UserLoginSession).where(UserLoginSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def add(self, login_session: UserLoginSession) -> UserLoginSession:
        self.session.add(login_session)
        await self.session.flush()
        return login_session

    async def close_session(self, login_session: UserLoginSession) -> None:
        login_session.is_active = False
        login_session.logout_at = datetime.now(UTC)
        await self.session.flush()
