from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.domain import Brand, Category, Product, ProductVariant, Region


class CatalogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_regions(self) -> tuple[list[tuple[Region, int]], int]:
        statement = (
            select(Region, func.count(Product.id))
            .outerjoin(Product, (Product.region_id == Region.id) & Product.is_active)
            .where(Region.is_active)
            .group_by(Region.id)
            .order_by(Region.display_order, Region.name)
        )
        rows = list((await self.session.execute(statement)).tuples())
        total_count = len(rows)
        return rows, total_count

    async def list_categories(self) -> list[Category]:
        return list(
            await self.session.scalars(
                select(Category).where(Category.is_active).order_by(Category.name)
            )
        )

    async def list_brands(self, *, region_id: int | None = None) -> list[Brand]:
        statement = select(Brand).where(Brand.is_active).order_by(Brand.name)
        if region_id is not None:
            region_sub = select(Region.id).where(Region.int_id == region_id).scalar_subquery()
            statement = statement.where(Brand.region_id == region_sub)
        return list(await self.session.scalars(statement))

    async def list_products(
        self,
        *,
        region_id: int | None,
        category_id: int | None,
        brand_id: int | None,
        search: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Product], int]:
        filters = [Product.is_active]
        if region_id:
            region_sub = select(Region.id).where(Region.int_id == region_id).scalar_subquery()
            filters.append(Product.region_id == region_sub)
        if category_id:
            cat_sub = select(Category.id).where(Category.int_id == category_id).scalar_subquery()
            filters.append(Product.category_id == cat_sub)
        if brand_id:
            brand_sub = select(Brand.id).where(Brand.int_id == brand_id).scalar_subquery()
            filters.append(Product.brand_id == brand_sub)
        if search:
            term = f"%{search.strip()}%"
            filters.append(or_(Product.name.ilike(term), Product.description.ilike(term)))

        total = await self.session.scalar(select(func.count(Product.id)).where(*filters)) or 0
        statement = (
            select(Product)
            .where(*filters)
            .options(
                selectinload(Product.region),
                selectinload(Product.category),
                selectinload(Product.brand),
                selectinload(Product.variants),
            )
            .order_by(Product.name)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(await self.session.scalars(statement)), total

    async def get_product(self, product_id: int, *, active_only: bool = True) -> Product | None:
        statement = (
            select(Product)
            .where(Product.int_id == product_id)
            .options(
                selectinload(Product.region),
                selectinload(Product.category),
                selectinload(Product.brand),
                selectinload(Product.variants),
            )
        )
        if active_only:
            statement = statement.where(Product.is_active)
        return await self.session.scalar(statement)

    async def get_region(self, region_id: int) -> Region | None:
        return await self.session.scalar(select(Region).where(Region.int_id == region_id))

    async def get_brand(self, brand_id: int) -> Brand | None:
        return await self.session.scalar(select(Brand).where(Brand.int_id == brand_id))

    async def get_category(self, category_id: int) -> Category | None:
        return await self.session.scalar(select(Category).where(Category.int_id == category_id))

    async def get_variant(
        self, variant_id: int, *, for_update: bool = False
    ) -> ProductVariant | None:
        statement = (
            select(ProductVariant)
            .where(ProductVariant.int_id == variant_id)
            .options(selectinload(ProductVariant.product).selectinload(Product.brand))
        )
        if for_update:
            statement = statement.with_for_update()
        return await self.session.scalar(statement)
