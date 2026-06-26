from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class RegionData(BaseModel):
    id: int = Field(validation_alias="int_id", serialization_alias="id")
    name: str
    slug: str
    subtitle: str | None
    description: str | None
    image_url: str | None
    product_count: int = 0

    model_config = {"from_attributes": True, "populate_by_name": True}


class CategoryData(BaseModel):
    id: int = Field(validation_alias="int_id", serialization_alias="id")
    name: str
    slug: str

    model_config = {"from_attributes": True, "populate_by_name": True}


class BrandData(BaseModel):
    id: int = Field(validation_alias="int_id", serialization_alias="id")
    name: str
    slug: str
    logo_url: str | None

    model_config = {"from_attributes": True, "populate_by_name": True}


class ProductVariantData(BaseModel):
    id: int = Field(validation_alias="int_id", serialization_alias="id")
    size: str
    price: Decimal
    stock_quantity: int
    is_available: bool

    model_config = {"from_attributes": True, "populate_by_name": True}


class ProductData(BaseModel):
    id: int = Field(validation_alias="int_id", serialization_alias="id")
    sku: str
    name: str
    slug: str
    description: str | None
    image_url: str | None
    tax_rate: Decimal
    region: RegionData | None
    category: CategoryData | None
    brand: BrandData | None
    variants: list[ProductVariantData]

    model_config = {"from_attributes": True, "populate_by_name": True}


class PaginatedProducts(BaseModel):
    items: list[ProductData]
    page: int
    page_size: int
    total: int


class CatalogProductVariant(BaseModel):
    id: int = Field(validation_alias="int_id", serialization_alias="id")
    size: str
    mrp: Decimal
    offer_price: Decimal
    discount_percentage: int
    stock_quantity: int
    is_available: bool

    model_config = {"from_attributes": True, "populate_by_name": True}


class CatalogProductItem(BaseModel):
    id: int = Field(validation_alias="int_id", serialization_alias="id")
    sku: str
    name: str
    subtitle: str | None = None
    description: str | None
    image_url: str | None
    variants: list[CatalogProductVariant]

    model_config = {"from_attributes": True, "populate_by_name": True}


class ProductListFilter(BaseModel):
    region_id: int | None = None
    region_name: str | None = None
    brand_id: int | None = None
    brand_name: str | None = None
    category_id: int | None = None
    category_name: str | None = None


class ProductListPagination(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class CatalogProductsListData(BaseModel):
    selected_filter: ProductListFilter
    items: list[CatalogProductItem]
    pagination: ProductListPagination


class ResponseMeta(BaseModel):
    timestamp: datetime
    request_id: str


class CatalogProductsResponse(BaseModel):
    status: bool = True
    code: int = 200
    message: str
    error: None = None
    data: CatalogProductsListData
    meta: ResponseMeta
