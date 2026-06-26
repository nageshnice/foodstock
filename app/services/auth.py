from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.security import create_access_token, hash_password, verify_password
from app.models.domain import Cart, User, UserLoginSession
from app.repositories.login_session import LoginSessionRepository
from app.repositories.user import UserRepository
from app.schemas.auth import AuthUser, LoginRequest, SignupRequest, TokenData
from app.services.api_keys import ApiKeyService


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.sessions = LoginSessionRepository(session)
        self.api_keys = ApiKeyService(session)

    async def signup(self, payload: SignupRequest, request: Request) -> TokenData:
        email = str(payload.email).lower()
        if await self.users.get_by_email(email):
            raise AppException("An account with this email already exists", code="email_exists")

        user = await self.users.add(
            User(email=email, password_hash=hash_password(payload.password))
        )
        self.session.add(Cart(user_id=user.id))
        await self.session.flush()
        return await self._complete_login(user, request)

    async def login(self, payload: LoginRequest, request: Request) -> TokenData:
        user = await self.users.get_by_email(str(payload.email).lower())
        if not user or not verify_password(payload.password, user.password_hash):
            raise AppException(
                "Invalid email or password", status_code=401, code="invalid_credentials"
            )
        if not user.is_active:
            raise AppException("Account is disabled", status_code=403, code="account_disabled")
        return await self._complete_login(user, request)

    async def logout(self, user: User, session_id: str | None) -> None:
        if session_id:
            from uuid import UUID

            try:
                sid = UUID(session_id)
            except ValueError:
                sid = None
            if sid:
                login_session = await self.sessions.get_by_id(sid)
                if login_session and login_session.user_id == user.id and login_session.is_active:
                    await self.sessions.close_session(login_session)
                    await self.api_keys.revoke_for_session(sid)
        else:
            await self.api_keys.revoke_for_user(user.id)
        await self.session.commit()

    async def _complete_login(self, user: User, request: Request) -> TokenData:
        login_session = await self.sessions.add(
            UserLoginSession(
                user_id=user.id,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
        )
        raw_api_key = await self.api_keys.issue_for_login(user, login_session)
        await self.session.commit()

        token = create_access_token(
            str(user.id),
            {"role": user.role.value, "session_id": str(login_session.id)},
        )
        return TokenData(
            access_token=token,
            api_key=raw_api_key,
            session_id=str(login_session.id),
            user=AuthUser.model_validate(user),
        )
