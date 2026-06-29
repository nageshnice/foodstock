from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.core.permissions import Role
from app.models.domain import OrderStatus


class NamedEntityInput(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    is_active: bool = True


class RegionAdminInput(NamedEntityInput):
    subtitle: str | None = Field(default=None, max_length=200)
    description: str | None = None
    image_url: str | None = None
    display_order: int = 0


class CategoryAdminInput(NamedEntityInput):
    description: str | None = None


class BrandAdminInput(NamedEntityInput):
    logo_url: str | None = None


class VendorAdminInput(NamedEntityInput):
    contact_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None
    tax_identifier: str | None = None


class VariantAdminInput(BaseModel):
    size: str = Field(min_length=1, max_length=100)
    mrp: Decimal = Field(default=Decimal("0.00"), ge=0)
    price: Decimal = Field(ge=0)
    stock_quantity: int = Field(ge=0)
    low_stock_threshold: int = Field(default=5, ge=0)
    is_active: bool = True

    @model_validator(mode="after")
    def normalize_pricing(self) -> "VariantAdminInput":
        if self.mrp <= 0:
            self.mrp = self.price
        if self.mrp < self.price:
            raise ValueError("MRP must be greater than or equal to offer price")
        return self


class ProductAdminInput(BaseModel):
    sku: str = Field(min_length=2, max_length=80)
    name: str = Field(min_length=2, max_length=200)
    description: str | None = None
    image_url: str | None = None
    tax_rate: Decimal = Field(default=Decimal("5.00"), ge=0)
    is_active: bool = False
    region_id: int | None = None
    category_id: int | None = None
    brand_id: int | None = None
    vendor_id: int | None = None
    variants: list[VariantAdminInput] = Field(min_length=1)


class InventoryAdjustment(BaseModel):
    quantity_change: int
    note: str = Field(min_length=2, max_length=500)


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class CustomerRoleUpdate(BaseModel):
    role: Role
    is_active: bool


class CustomerCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=160)
    phone: str | None = Field(default=None, max_length=24)
    role: Role = Role.CUSTOMER
    is_active: bool = True


class DashboardData(BaseModel):
    products: int
    active_products: int
    low_stock_variants: int
    customers: int
    orders: int
    revenue: Decimal
    pending_orders: int = 0
    today_orders: int = 0
    today_revenue: Decimal = Decimal("0.00")
    avg_order_value: Decimal = Decimal("0.00")
    sales_trend: list["DailySalesPoint"] = Field(default_factory=list)
    orders_by_status: list["StatusBreakdown"] = Field(default_factory=list)
    top_products: list["TopProductSummary"] = Field(default_factory=list)
    recent_orders: list["RecentOrderSummary"] = Field(default_factory=list)


class DailySalesPoint(BaseModel):
    date: str
    orders: int
    revenue: Decimal


class StatusBreakdown(BaseModel):
    status: OrderStatus
    count: int


class TopProductSummary(BaseModel):
    name: str
    quantity: int
    revenue: Decimal


class RecentOrderSummary(BaseModel):
    id: int = Field(validation_alias="int_id", serialization_alias="id")
    order_number: str
    status: OrderStatus
    total_amount: Decimal
    placed_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class AdminProfileData(BaseModel):
    id: int = Field(validation_alias="int_id", serialization_alias="id")
    email: EmailStr
    full_name: str | None
    phone: str | None
    image_url: str | None
    role: Role

    model_config = {"from_attributes": True, "populate_by_name": True}


class AdminAlert(BaseModel):
    id: str
    severity: str
    title: str
    message: str
    href: str | None = None


class EntityData(BaseModel):
    id: int = Field(validation_alias="int_id", serialization_alias="id")
    name: str
    is_active: bool
    product_count: int = 0
    subtitle: str | None = None
    description: str | None = None
    image_url: str | None = None
    logo_url: str | None = None
    display_order: int | None = None

    model_config = {"from_attributes": True, "populate_by_name": True}


class VendorData(BaseModel):
    id: int = Field(validation_alias="int_id", serialization_alias="id")
    name: str
    is_active: bool
    contact_name: str | None
    email: str | None
    phone: str | None
    address: str | None
    tax_identifier: str | None

    model_config = {"from_attributes": True, "populate_by_name": True}


class AdminVariantData(VariantAdminInput):
    id: int = Field(validation_alias="int_id", serialization_alias="id")

    model_config = {"from_attributes": True, "populate_by_name": True}


class AdminProductData(BaseModel):
    id: int = Field(validation_alias="int_id", serialization_alias="id")
    sku: str
    name: str
    source_section: str | None
    description: str | None
    image_url: str | None
    tax_rate: Decimal
    is_active: bool
    region_id: int | None = None
    category_id: int | None = None
    brand_id: int | None = None
    vendor_id: int | None = None
    region_name: str | None = None
    category_name: str | None = None
    brand_name: str | None = None
    vendor_name: str | None = None
    variants: list[AdminVariantData]

    model_config = {"from_attributes": True, "populate_by_name": True}


class CustomerAdminData(BaseModel):
    id: int = Field(validation_alias="int_id", serialization_alias="id")
    email: EmailStr
    full_name: str | None
    phone: str | None
    image_url: str | None = None
    role: Role
    is_active: bool
    created_at: datetime
    addresses_count: int = 0
    orders_count: int = 0
    total_spent: Decimal = Decimal("0.00")

    model_config = {"from_attributes": True, "populate_by_name": True}
