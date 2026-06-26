from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.domain import OrderStatus, PaymentMethod
from app.schemas.cart import CartData
from app.schemas.customer import AddressData


class CheckoutRequest(BaseModel):
    address_id: int
    payment_method: PaymentMethod = PaymentMethod.UPI_ON_DELIVERY
    promo_code: str | None = None


class CheckoutData(BaseModel):
    cart: CartData
    address: AddressData
    payment_method: PaymentMethod
    minimum_order_met: bool


class OrderItemData(BaseModel):
    product_name: str
    variant_size: str
    unit_price: Decimal
    quantity: int
    line_total: Decimal

    model_config = {"from_attributes": True}


class OrderData(BaseModel):
    id: int = Field(validation_alias="int_id", serialization_alias="id")
    order_number: str
    status: OrderStatus
    payment_method: PaymentMethod
    subtotal: Decimal
    tax_amount: Decimal
    delivery_fee: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    delivery_address: str
    placed_at: datetime
    items: list[OrderItemData]

    model_config = {"from_attributes": True, "populate_by_name": True}
