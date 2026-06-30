from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    event,
    func,
    select,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.permissions import Role
from app.database.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class AddressType(StrEnum):
    HOME = "home"
    OFFICE = "office"
    OTHER = "other"


class InventoryTransactionType(StrEnum):
    PURCHASE = "purchase"
    ADJUSTMENT = "adjustment"
    RETURN = "return"
    SALE = "sale"


class OrderStatus(StrEnum):
    PLACED = "placed"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    DISPATCHED = "dispatched"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class PaymentMethod(StrEnum):
    COD = "cod"
    RAZORPAY = "razorpay"
    UPI_ON_DELIVERY = "upi_on_delivery"


# Helper: public integer ID used by API clients. UUID remains the internal primary key.
def _int_id(table: str) -> Mapped[int]:
    return mapped_column(
        BigInteger,
        unique=True,
        index=True,
    )


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    int_id: Mapped[int] = _int_id("users")
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str | None] = mapped_column(String(160))
    phone: Mapped[str | None] = mapped_column(String(24), unique=True)
    image_url: Mapped[str | None] = mapped_column(String(500))
    role: Mapped[Role] = mapped_column(
        Enum(Role, native_enum=False, length=32), default=Role.CUSTOMER, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    addresses: Mapped[list["Address"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    login_sessions: Mapped[list["UserLoginSession"]] = relationship(back_populates="user")
    api_keys: Mapped[list["UserApiKey"]] = relationship(back_populates="user")


class UserLoginSession(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "user_login_sessions"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    login_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    logout_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    user: Mapped[User] = relationship(back_populates="login_sessions")
    api_keys: Mapped[list["UserApiKey"]] = relationship(back_populates="session")


class UserApiKey(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_api_keys"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    session_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("user_login_sessions.id"), index=True
    )
    key_prefix: Mapped[str] = mapped_column(String(16), index=True)
    key_hash: Mapped[str] = mapped_column(String(255))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    user: Mapped[User] = relationship(back_populates="api_keys")
    session: Mapped[UserLoginSession | None] = relationship(back_populates="api_keys")


class Region(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "regions"

    int_id: Mapped[int] = _int_id("regions")
    name: Mapped[str] = mapped_column(String(100), unique=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    subtitle: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(500))
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)


class Category(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "categories"

    int_id: Mapped[int] = _int_id("categories")
    name: Mapped[str] = mapped_column(String(100), unique=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)


class Brand(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "brands"
    __table_args__ = (UniqueConstraint("region_id", "name", name="uq_brands_region_name"),)

    int_id: Mapped[int] = _int_id("brands")
    name: Mapped[str] = mapped_column(String(120), index=True)
    slug: Mapped[str] = mapped_column(String(140), unique=True, index=True)
    logo_url: Mapped[str | None] = mapped_column(String(500))
    region_id: Mapped[UUID | None] = mapped_column(ForeignKey("regions.id"), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    region: Mapped[Region | None] = relationship()


class Vendor(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "vendors"

    int_id: Mapped[int] = _int_id("vendors")
    name: Mapped[str] = mapped_column(String(160), unique=True)
    contact_name: Mapped[str | None] = mapped_column(String(160))
    email: Mapped[str | None] = mapped_column(String(320))
    phone: Mapped[str | None] = mapped_column(String(24))
    address: Mapped[str | None] = mapped_column(Text)
    tax_identifier: Mapped[str | None] = mapped_column(String(64))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)


class Product(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "products"

    int_id: Mapped[int] = _int_id("products")
    sku: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    slug: Mapped[str] = mapped_column(String(240), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    source_section: Mapped[str | None] = mapped_column(String(120))
    image_url: Mapped[str | None] = mapped_column(String(500))
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("5.00"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    region_id: Mapped[UUID | None] = mapped_column(ForeignKey("regions.id"), index=True)
    category_id: Mapped[UUID | None] = mapped_column(ForeignKey("categories.id"), index=True)
    brand_id: Mapped[UUID | None] = mapped_column(ForeignKey("brands.id"), index=True)
    vendor_id: Mapped[UUID | None] = mapped_column(ForeignKey("vendors.id"), index=True)

    region: Mapped[Region | None] = relationship()
    category: Mapped[Category | None] = relationship()
    brand: Mapped[Brand | None] = relationship()
    vendor: Mapped[Vendor | None] = relationship()
    variants: Mapped[list["ProductVariant"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", lazy="selectin"
    )


class ProductVariant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "product_variants"
    __table_args__ = (UniqueConstraint("product_id", "size", name="uq_variant_product_size"),)

    int_id: Mapped[int] = _int_id("product_variants")
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    size: Mapped[str] = mapped_column(String(100))
    mrp: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)
    low_stock_threshold: Mapped[int] = mapped_column(Integer, default=5)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)

    product: Mapped[Product] = relationship(back_populates="variants")


class InventoryTransaction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "inventory_transactions"

    variant_id: Mapped[UUID] = mapped_column(ForeignKey("product_variants.id"), index=True)
    quantity_change: Mapped[int] = mapped_column(Integer)
    transaction_type: Mapped[InventoryTransactionType] = mapped_column(
        Enum(InventoryTransactionType, native_enum=False, length=32)
    )
    note: Mapped[str | None] = mapped_column(String(500))
    created_by_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))


class Cart(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "carts"

    int_id: Mapped[int] = _int_id("carts")
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    items: Mapped[list["CartItem"]] = relationship(
        back_populates="cart", cascade="all, delete-orphan", lazy="raise"
    )


class CartItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "cart_items"
    __table_args__ = (UniqueConstraint("cart_id", "variant_id", name="uq_cart_variant"),)

    int_id: Mapped[int] = _int_id("cart_items")
    cart_id: Mapped[UUID] = mapped_column(ForeignKey("carts.id", ondelete="CASCADE"))
    variant_id: Mapped[UUID] = mapped_column(ForeignKey("product_variants.id"))
    quantity: Mapped[int] = mapped_column(Integer)

    cart: Mapped[Cart] = relationship(back_populates="items")
    variant: Mapped[ProductVariant] = relationship(lazy="raise")


class Address(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "addresses"

    int_id: Mapped[int] = _int_id("addresses")
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    address_type: Mapped[AddressType] = mapped_column(
        Enum(AddressType, native_enum=False, length=20)
    )
    house_flat_floor: Mapped[str] = mapped_column(String(160))
    building_street: Mapped[str | None] = mapped_column(String(200))
    area_locality: Mapped[str] = mapped_column(String(160))
    city: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(100))
    pincode: Mapped[str] = mapped_column(String(10), index=True)
    landmark: Mapped[str | None] = mapped_column(String(160))
    delivery_instructions: Mapped[str | None] = mapped_column(String(500))
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped[User] = relationship(back_populates="addresses")


class Order(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "orders"

    int_id: Mapped[int] = _int_id("orders")
    order_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    address_id: Mapped[UUID | None] = mapped_column(ForeignKey("addresses.id"))
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, native_enum=False, length=32), default=OrderStatus.PLACED, index=True
    )
    payment_method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, native_enum=False, length=32)
    )
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    delivery_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    delivery_address: Mapped[str] = mapped_column(Text)
    placed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", lazy="selectin"
    )


class OrderItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "order_items"

    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    product_id: Mapped[UUID | None] = mapped_column(ForeignKey("products.id"))
    variant_id: Mapped[UUID | None] = mapped_column(ForeignKey("product_variants.id"))
    product_int_id: Mapped[int | None] = mapped_column(BigInteger, index=True)
    variant_int_id: Mapped[int | None] = mapped_column(BigInteger, index=True)
    product_name: Mapped[str] = mapped_column(String(200))
    brand_name: Mapped[str | None] = mapped_column(String(160))
    image_url: Mapped[str | None] = mapped_column(String(500))
    variant_size: Mapped[str] = mapped_column(String(100))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    quantity: Mapped[int] = mapped_column(Integer)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    order: Mapped[Order] = relationship(back_populates="items")


def _assign_public_int_id(mapper: object, connection: object, target: object) -> None:
    if getattr(target, "int_id", None) is not None:
        return
    table = target.__table__
    counter_key = f"_next_int_id_{table.name}"
    next_id = connection.info.get(counter_key)
    if next_id is None:
        next_id = connection.execute(
            select(func.coalesce(func.max(table.c.int_id), 0))
        ).scalar_one()
    next_id = int(next_id) + 1
    connection.info[counter_key] = next_id
    target.int_id = next_id


for _model in (
    User,
    Region,
    Category,
    Brand,
    Vendor,
    Product,
    ProductVariant,
    Cart,
    CartItem,
    Address,
    Order,
):
    event.listen(_model, "before_insert", _assign_public_int_id)
