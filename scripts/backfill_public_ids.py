import asyncio

from sqlalchemy import text

from app.database.session import AsyncSessionFactory, close_database

STATEMENTS = [
    "create sequence if not exists carts_int_id_seq",
    "alter table carts add column if not exists int_id bigint",
    "update carts set int_id = nextval('carts_int_id_seq') where int_id is null",
    "alter table carts alter column int_id set default nextval('carts_int_id_seq')",
    "alter table carts alter column int_id set not null",
    "create unique index if not exists ix_carts_int_id on carts (int_id)",
    "create sequence if not exists cart_items_int_id_seq",
    "alter table cart_items add column if not exists int_id bigint",
    "update cart_items set int_id = nextval('cart_items_int_id_seq') where int_id is null",
    "alter table cart_items alter column int_id set default nextval('cart_items_int_id_seq')",
    "alter table cart_items alter column int_id set not null",
    "create unique index if not exists ix_cart_items_int_id on cart_items (int_id)",
]


async def main() -> None:
    async with AsyncSessionFactory() as session:
        for statement in STATEMENTS:
            await session.execute(text(statement))
        await session.commit()
    await close_database()
    print("Public integer IDs are ready.")


if __name__ == "__main__":
    asyncio.run(main())
