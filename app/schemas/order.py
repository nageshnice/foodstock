from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.domain import OrderStatus, PaymentMethod
from app.schemas.cart import CartData
from app.schemas.customer import AddressData


class CheckoutRequest(BaseModel):
    address_id: int = Field(description="Saved address id from GET /customer/addresses")
    payment_method: PaymentMethod = Field(
        default=PaymentMethod.COD,
        description="Payment method: cod, upi_on_delivery, or razorpay",
    )
    promo_code: str | None = Field(
        default=None,
        description="Optional promo code (reserved for a future release)",
    )


class CheckoutBillSummary(BaseModel):
    item_count: int = Field(description="Total units in cart (sum of line quantities)")
    line_count: int = Field(description="Number of cart lines (distinct variants)")
    subtotal: Decimal = Field(description="Sum of line totals before tax and delivery")
    delivery_fee: Decimal
    tax_amount: Decimal
    total_amount: Decimal = Field(description="Subtotal + tax + delivery fee")
    minimum_order_amount: Decimal
    minimum_order_met: bool
    free_delivery_threshold: Decimal


class CheckoutData(BaseModel):
    cart: CartData = Field(description="Cart lines with per-variant quantity and pricing")
    address: AddressData
    payment_method: PaymentMethod
    minimum_order_met: bool
    bill_summary: CheckoutBillSummary = Field(
        description="Checkout screen totals (subtotal, tax, delivery, grand total)"
    )


class OrderItemData(BaseModel):
    variant_id: int
    product_id: int
    product_name: str
    brand_name: str | None = None
    image_url: str | None = None
    variant_size: str
    unit_price: Decimal
    quantity: int
    tax_rate: Decimal
    tax_amount: Decimal
    line_total: Decimal


class OrderPaymentInfo(BaseModel):
    method: PaymentMethod
    status: str = Field(
        description="paid | pay_on_delivery | pending_online (razorpay not live yet)"
    )
    label: str
    requires_online_payment: bool = False


class OrderData(BaseModel):
    id: int = Field(validation_alias="int_id", serialization_alias="id")
    order_number: str
    status: OrderStatus
    payment_method: PaymentMethod
    payment: OrderPaymentInfo
    subtotal: Decimal
    tax_amount: Decimal
    delivery_fee: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    delivery_address: str
    placed_at: datetime
    bill_summary: CheckoutBillSummary
    items: list[OrderItemData]

    model_config = {"populate_by_name": True}
