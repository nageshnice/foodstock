from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.security import create_access_token, hash_password, verify_password
from app.models.domain import Cart, User
from app.repositories.user import UserRepository
from app.schemas.auth import AuthUser, LoginRequest, SignupRequest, TokenData


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)

    async def signup(self, payload: SignupRequest) -> TokenData:
        email = str(payload.email).lower()
        if await self.users.get_by_email(email):
            raise AppException("An account with this email already exists", code="email_exists")

        user = await self.users.add(
            User(email=email, password_hash=hash_password(payload.password))
        )
        self.session.add(Cart(user_id=user.id))
        await self.session.flush()
        return self._token_data(user)

    async def login(self, payload: LoginRequest) -> TokenData:
        user = await self.users.get_by_email(str(payload.email).lower())
        if not user or not verify_password(payload.password, user.password_hash):
            raise AppException(
                "Invalid email or password", status_code=401, code="invalid_credentials"
            )
        if not user.is_active:
            raise AppException("Account is disabled", status_code=403, code="account_disabled")
        return self._token_data(user)

    @staticmethod
    def _token_data(user: User) -> TokenData:
        token = create_access_token(str(user.id), {"role": user.role.value})
        return TokenData(access_token=token, user=AuthUser.model_validate(user))
