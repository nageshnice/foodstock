import asyncio

from app.core.config import get_settings
from app.core.permissions import Role
from app.core.security import hash_password
from app.database.session import AsyncSessionFactory, close_database
from app.models.domain import User
from app.repositories.user import UserRepository


async def main() -> None:
    settings = get_settings()
    if not settings.bootstrap_admin_email or not settings.bootstrap_admin_password:
        raise RuntimeError(
            "Set BOOTSTRAP_ADMIN_EMAIL and BOOTSTRAP_ADMIN_PASSWORD before running this command."
        )
    async with AsyncSessionFactory() as session:
        repository = UserRepository(session)
        email = settings.bootstrap_admin_email.lower()
        user = await repository.get_by_email(email)
        if user:
            user.role = Role.SUPER_ADMIN
            user.is_active = True
            user.password_hash = hash_password(settings.bootstrap_admin_password.get_secret_value())
        else:
            session.add(
                User(
                    email=email,
                    password_hash=hash_password(
                        settings.bootstrap_admin_password.get_secret_value()
                    ),
                    role=Role.SUPER_ADMIN,
                    is_active=True,
                )
            )
        await session.commit()
    await close_database()
    print(f"Super admin ready: {email}")


if __name__ == "__main__":
    asyncio.run(main())
