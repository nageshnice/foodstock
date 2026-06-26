from decimal import Decimal

from pydantic import BaseModel, Field


class CartItemInput(BaseModel):
    variant_id: int
    quantity: int = Field(ge=1, le=99)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=0, le=99)


class CartItemData(BaseModel):
    id: int
    variant_id: int
    product_id: int
    product_name: str
    brand_name: str | None
    image_url: str | None
    size: str
    unit_price: Decimal
    quantity: int
    line_total: Decimal


class CartData(BaseModel):
    id: int
    items: list[CartItemData]
    item_count: int
    subtotal: Decimal
    tax_amount: Decimal
    delivery_fee: Decimal
    total_amount: Decimal
