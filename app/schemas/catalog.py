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
