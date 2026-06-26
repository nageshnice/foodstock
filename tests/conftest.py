import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

os.environ.setdefault(
    "DATABASE_URL",
    "mysql+aiomysql://root:@localhost:3306/test_food_stock",
)
os.environ.setdefault("JWT_SECRET", "test-secret-value-that-is-at-least-32-characters")

from app.database.base import Base  # noqa: E402
from app.database.session import get_db_session  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def api_client() -> TestClient:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_session():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def create_schema() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    app.dependency_overrides[get_db_session] = override_session
    with TestClient(app) as client:
        client.portal.call(create_schema)
        yield client
    app.dependency_overrides.clear()
