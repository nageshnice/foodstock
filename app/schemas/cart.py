from decimal import Decimal

from pydantic import BaseModel, Field

_MONEY_EXAMPLE = "199.00"


class CartItemInput(BaseModel):
    variant_id: int = Field(json_schema_extra={"examples": [12]})
    quantity: int = Field(ge=1, le=99, json_schema_extra={"examples": [1]})


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=0, le=99, json_schema_extra={"examples": [2]})


class CartItemData(BaseModel):
    id: int
    variant_id: int
    product_id: int
    product_name: str
    brand_name: str | None
    image_url: str | None
    size: str
    unit_price: Decimal = Field(json_schema_extra={"examples": [_MONEY_EXAMPLE]})
    quantity: int
    line_total: Decimal = Field(json_schema_extra={"examples": [_MONEY_EXAMPLE]})


class CartData(BaseModel):
    id: int
    items: list[CartItemData]
    item_count: int
    subtotal: Decimal = Field(json_schema_extra={"examples": [_MONEY_EXAMPLE]})
    tax_amount: Decimal = Field(json_schema_extra={"examples": ["9.95"]})
    delivery_fee: Decimal = Field(json_schema_extra={"examples": ["5.00"]})
    total_amount: Decimal = Field(json_schema_extra={"examples": ["213.95"]})
