import pytest
from sqlalchemy.ext.asyncio import create_async_engine

import app.models  # noqa: F401
from app.database.base import Base


@pytest.mark.asyncio
async def test_complete_schema_can_be_created() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    table_names = set(Base.metadata.tables)
    assert {
        "users",
        "regions",
        "categories",
        "brands",
        "vendors",
        "products",
        "product_variants",
        "carts",
        "cart_items",
        "addresses",
        "orders",
        "order_items",
        "inventory_transactions",
    } <= table_names
    await engine.dispose()
