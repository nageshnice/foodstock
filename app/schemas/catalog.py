from datetime import datetime
from decimal import Decimal
from typing import Literal

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
    mrp: Decimal
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
    cart_added: Literal["yes", "no"] = "no"
    variants: list[CatalogProductVariant]

    model_config = {"from_attributes": True, "populate_by_name": True}


class CatalogCartInfo(BaseModel):
    item_count: int = Field(description="Total quantity of units in the cart")
    items_total: Decimal = Field(description="Subtotal of cart line items before tax and delivery")
    total_amount: Decimal = Field(description="Cart total including tax and delivery")


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
    cart_info: CatalogCartInfo
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
