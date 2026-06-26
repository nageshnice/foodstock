from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.domain import Product
from app.repositories.catalog import CatalogRepository
from app.schemas.catalog import (
    BrandData,
    CategoryData,
    PaginatedProducts,
    ProductData,
    ProductVariantData,
    RegionData,
)


class CatalogService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = CatalogRepository(session)

    async def regions(self) -> list[RegionData]:
        rows, total_count = await self.repository.list_regions()
        return [
            RegionData.model_validate(region).model_copy(
                update={"product_count": count, "total_count": total_count}
            )
            for region, count in rows
        ]

    async def categories(self) -> list[CategoryData]:
        return [
            CategoryData.model_validate(item) for item in await self.repository.list_categories()
        ]

    async def brands(self, region_id: int | None) -> list[BrandData]:
        return [
            BrandData.model_validate(item) for item in await self.repository.list_brands(region_id)
        ]

    async def products(
        self,
        *,
        region_id: int | None,
        category_id: int | None,
        brand_id: int | None,
        search: str | None,
        page: int,
        page_size: int,
    ) -> PaginatedProducts:
        products, total = await self.repository.list_products(
            region_id=region_id,
            category_id=category_id,
            brand_id=brand_id,
            search=search,
            page=page,
            page_size=page_size,
        )
        return PaginatedProducts(
            items=[self._serialize_product(product) for product in products],
            page=page,
            page_size=page_size,
            total=total,
        )

    async def product(self, product_id: int) -> ProductData:
        product = await self.repository.get_product(product_id)
        if not product:
            raise AppException("Product not found", status_code=404, code="product_not_found")
        return self._serialize_product(product)

    @staticmethod
    def _serialize_product(product: Product) -> ProductData:
        variants = [
            ProductVariantData(
                int_id=item.int_id,
                size=item.size,
                price=item.price,
                stock_quantity=item.stock_quantity,
                is_available=item.is_active and item.stock_quantity > 0,
            )
            for item in product.variants
            if item.is_active
        ]
        return ProductData(
            int_id=product.int_id,
            sku=product.sku,
            name=product.name,
            slug=product.slug,
            description=product.description,
            image_url=product.image_url,
            tax_rate=product.tax_rate,
            region=RegionData.model_validate(product.region) if product.region else None,
            category=CategoryData.model_validate(product.category) if product.category else None,
            brand=BrandData.model_validate(product.brand) if product.brand else None,
            variants=variants,
        )
