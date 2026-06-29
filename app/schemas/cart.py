from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

_MONEY_EXAMPLE = "199.00"
_EMPTY_CART_EXAMPLE = {
    "id": 1,
    "items": [],
    "item_count": 0,
    "subtotal": "0.00",
    "tax_amount": "0.00",
    "delivery_fee": "0.00",
    "total_amount": "0.00",
}


class CartItemInput(BaseModel):
    variant_id: int = Field(
        description="Product variant id from catalog products (variants[].id).",
        json_schema_extra={"examples": [2]},
    )
    quantity: int = Field(ge=1, le=99, json_schema_extra={"examples": [1]})
    replace: bool = Field(
        default=False,
        description="When false (default), quantity is added to any existing line for this variant. When true, sets the line quantity to this value.",
        json_schema_extra={"examples": [False]},
    )


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=0, le=99, json_schema_extra={"examples": [2]})


class CartItemData(BaseModel):
    id: int = Field(json_schema_extra={"examples": [12]})
    variant_id: int = Field(json_schema_extra={"examples": [12]})
    product_id: int = Field(json_schema_extra={"examples": [5]})
    product_name: str = Field(json_schema_extra={"examples": ["Five Spice Powder"]})
    brand_name: str | None = Field(json_schema_extra={"examples": ["Exotic Pantry"]})
    image_url: str | None = None
    size: str = Field(json_schema_extra={"examples": ["100g"]})
    unit_price: Decimal = Field(json_schema_extra={"examples": [_MONEY_EXAMPLE]})
    quantity: int = Field(json_schema_extra={"examples": [1]})
    line_total: Decimal = Field(json_schema_extra={"examples": [_MONEY_EXAMPLE]})


class CartData(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [_EMPTY_CART_EXAMPLE]})

    id: int
    items: list[CartItemData]
    item_count: int
    subtotal: Decimal = Field(json_schema_extra={"examples": ["0.00"]})
    tax_amount: Decimal = Field(json_schema_extra={"examples": ["0.00"]})
    delivery_fee: Decimal = Field(json_schema_extra={"examples": ["0.00"]})
    total_amount: Decimal = Field(json_schema_extra={"examples": ["0.00"]})
