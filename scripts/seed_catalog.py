"""Seed catalog data for XAMPP MySQL development."""

import asyncio
from decimal import Decimal

from sqlalchemy import select

import app.models  # noqa: F401
from app.database.session import AsyncSessionFactory, close_database
from app.models.domain import Brand, Category, Product, ProductVariant, Region, Vendor
from app.utils.text import slugify


async def _get_or_create(session, model, name: str, **extra):
    item = await session.scalar(select(model).where(model.name == name))
    if item:
        return item
    values = {"name": name, **extra}
    if hasattr(model, "slug"):
        values["slug"] = slugify(name)
    item = model(**values)
    session.add(item)
    await session.flush()
    return item


async def main() -> None:
    async with AsyncSessionFactory() as session:
        japan = await _get_or_create(
            session,
            Region,
            "Japanese",
            subtitle="Authentic Japanese pantry",
            description="Soy sauce, miso, noodles, and specialty imports.",
            display_order=1,
        )
        korean = await _get_or_create(
            session,
            Region,
            "Korean",
            subtitle="K-food essentials",
            description="Kimchi bases, gochujang, and instant favorites.",
            display_order=2,
        )
        thai = await _get_or_create(
            session,
            Region,
            "Thai",
            subtitle="Thai cooking staples",
            description="Curry pastes, coconut milk, and aromatics.",
            display_order=3,
        )
        chinese = await _get_or_create(
            session,
            Region,
            "Chinese",
            subtitle="Wok and pantry classics",
            description="Sauces, noodles, and dim sum ingredients.",
            display_order=4,
        )

        sauces = await _get_or_create(
            session, Category, "Sauces & Condiments", description="Cooking and table sauces"
        )
        noodles = await _get_or_create(session, Category, "Noodles", description="Dry and fresh noodles")
        spices = await _get_or_create(session, Category, "Spices", description="Exotic spice blends")

        kikkoman = await _get_or_create(session, Brand, "Kikkoman")
        nongshim = await _get_or_create(session, Brand, "Nongshim")
        maesri = await _get_or_create(session, Brand, "Mae Sri")
        lee_kum_kee = await _get_or_create(session, Brand, "Lee Kum Kee")

        faridi = await _get_or_create(
            session,
            Vendor,
            "Faridi Impex",
            contact_name="Catalog Team",
            email="catalog@faridi.example",
            phone="+91-9876543210",
        )

        exotic = await _get_or_create(session, Brand, "Exotic Pantry")

        catalog = [
            (
                "JPN-SOY-001",
                "Kikkoman Soy Sauce",
                japan,
                sauces,
                kikkoman,
                [("250ml", Decimal("189.00"), 40), ("500ml", Decimal("329.00"), 25)],
            ),
            (
                "KOR-NOO-001",
                "Shin Ramyun Noodles",
                korean,
                noodles,
                nongshim,
                [("Pack of 5", Decimal("449.00"), 60), ("Pack of 10", Decimal("849.00"), 30)],
            ),
            (
                "THA-CUR-001",
                "Mae Sri Red Curry Paste",
                thai,
                sauces,
                maesri,
                [("114g", Decimal("129.00"), 18), ("400g", Decimal("349.00"), 12)],
            ),
            (
                "CHN-OYS-001",
                "Lee Kum Kee Oyster Sauce",
                chinese,
                sauces,
                lee_kum_kee,
                [("255g", Decimal("199.00"), 35)],
            ),
            (
                "EXO-SPC-001",
                "Five Spice Powder",
                chinese,
                spices,
                exotic,
                [("100g", Decimal("149.00"), 8), ("250g", Decimal("299.00"), 5)],
            ),
        ]

        created = 0
        for sku, name, region, category, brand, variants in catalog:
            exists = await session.scalar(select(Product).where(Product.sku == sku))
            if exists:
                continue
            product = Product(
                sku=sku,
                name=name,
                slug=slugify(name),
                description=f"Imported {name} for quick-commerce fulfilment.",
                tax_rate=Decimal("5.00"),
                is_active=True,
                region_id=region.id,
                category_id=category.id,
                brand_id=brand.id,
                vendor_id=faridi.id,
                variants=[
                    ProductVariant(
                        size=size,
                        price=price,
                        stock_quantity=stock,
                        low_stock_threshold=10,
                        is_active=True,
                    )
                    for size, price, stock in variants
                ],
            )
            session.add(product)
            await session.flush()
            created += 1

        await session.commit()
        print(f"Seed complete. Added {created} products.")

    await close_database()


if __name__ == "__main__":
    asyncio.run(main())
