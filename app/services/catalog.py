from decimal import Decimal
import math

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.domain import Brand, Category, Product, Region
from app.repositories.catalog import CatalogRepository
from app.schemas.catalog import (
    BrandData,
    CatalogProductItem,
    CatalogProductVariant,
    CatalogProductsListData,
    CategoryData,
    ProductData,
    ProductListFilter,
    ProductListPagination,
    ProductVariantData,
    RegionData,
)


class CatalogService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = CatalogRepository(session)

    async def regions(self) -> tuple[list[RegionData], int]:
        rows, total_count = await self.repository.list_regions()
        return [
            RegionData.model_validate(region).model_copy(update={"product_count": count})
            for region, count in rows
        ], total_count

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
    ) -> CatalogProductsListData:
        products, total = await self.repository.list_products(
            region_id=region_id,
            category_id=category_id,
            brand_id=brand_id,
            search=search,
            page=page,
            page_size=page_size,
        )
        selected_filter = await self._build_selected_filter(
            region_id=region_id,
            category_id=category_id,
            brand_id=brand_id,
        )
        total_pages = math.ceil(total / page_size) if page_size else 0
        return CatalogProductsListData(
            selected_filter=selected_filter,
            items=[self._serialize_catalog_product(product) for product in products],
            pagination=ProductListPagination(
                page=page,
                page_size=page_size,
                total=total,
                total_pages=total_pages,
            ),
        )

    async def _build_selected_filter(
        self,
        *,
        region_id: int | None,
        category_id: int | None,
        brand_id: int | None,
    ) -> ProductListFilter:
        region_name = None
        brand_name = None
        category_name = None

        if region_id is not None:
            region = await self.repository.get_region(region_id)
            region_name = region.name if region else None
        if brand_id is not None:
            brand = await self.repository.get_brand(brand_id)
            brand_name = brand.name if brand else None
        if category_id is not None:
            category = await self.repository.get_category(category_id)
            category_name = category.name if category else None

        return ProductListFilter(
            region_id=region_id,
            region_name=region_name,
            brand_id=brand_id,
            brand_name=brand_name,
            category_id=category_id,
            category_name=category_name,
        )

    async def product(self, product_id: int) -> ProductData:
        product = await self.repository.get_product(product_id)
        if not product:
            raise AppException("Product not found", status_code=404, code="product_not_found")
        return self._serialize_product(product)

    @staticmethod
    def _variant_pricing(mrp: Decimal, offer_price: Decimal) -> tuple[Decimal, Decimal, int]:
        effective_mrp = mrp if mrp > 0 else offer_price
        discount_percentage = 0
        if effective_mrp > 0 and offer_price < effective_mrp:
            discount_percentage = int(
                ((effective_mrp - offer_price) / effective_mrp * 100).quantize(Decimal("1"))
            )
        return effective_mrp, offer_price, max(discount_percentage, 0)

    @staticmethod
    def _serialize_catalog_product(product: Product) -> CatalogProductItem:
        variants = []
        for item in product.variants:
            if not item.is_active:
                continue
            mrp, offer_price, discount_percentage = CatalogService._variant_pricing(
                item.mrp, item.price
            )
            variants.append(
                CatalogProductVariant(
                    int_id=item.int_id,
                    size=item.size,
                    mrp=mrp,
                    offer_price=offer_price,
                    discount_percentage=discount_percentage,
                    stock_quantity=item.stock_quantity,
                    is_available=item.stock_quantity > 0,
                )
            )
        return CatalogProductItem(
            int_id=product.int_id,
            sku=product.sku,
            name=product.name,
            subtitle=product.source_section,
            description=product.description,
            image_url=product.image_url,
            variants=variants,
        )

    @staticmethod
    def _serialize_product(product: Product) -> ProductData:
        variants = [
            ProductVariantData(
                int_id=item.int_id,
                size=item.size,
                mrp=item.mrp if item.mrp > 0 else item.price,
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
