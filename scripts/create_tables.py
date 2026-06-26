import asyncio

import app.models  # noqa: F401
from app.database.base import Base
from app.database.session import close_database, engine


async def main() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    await close_database()
    print("Database tables created.")


if __name__ == "__main__":
    asyncio.run(main())
