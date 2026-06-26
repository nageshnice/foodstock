from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field

from app.models.domain import AddressType


class ProfileData(BaseModel):
    id: int = Field(validation_alias="int_id", serialization_alias="id")
    email: EmailStr
    full_name: str | None
    phone: str | None
    image_url: str | None

    model_config = {"from_attributes": True, "populate_by_name": True}


class ProfileUpdate(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    phone: str | None = Field(default=None, min_length=7, max_length=24)
    image_url: str | None = Field(default=None, max_length=500)


class AddressInput(BaseModel):
    address_type: AddressType
    house_flat_floor: str = Field(min_length=1, max_length=160)
    building_street: str | None = Field(default=None, max_length=200)
    area_locality: str = Field(min_length=2, max_length=160)
    city: str = Field(min_length=2, max_length=100)
    state: str = Field(min_length=2, max_length=100)
    pincode: str = Field(pattern=r"^[1-9][0-9]{5}$")
    landmark: str | None = Field(default=None, max_length=160)
    delivery_instructions: str | None = Field(default=None, max_length=500)
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    is_default: bool = False


class AddressData(AddressInput):
    id: int = Field(validation_alias="int_id", serialization_alias="id")

    model_config = {"from_attributes": True, "populate_by_name": True}
