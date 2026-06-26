from typing import Self

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.core.permissions import Role


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str

    @model_validator(mode="after")
    def passwords_match(self) -> Self:
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthUser(BaseModel):
    id: int = Field(validation_alias="int_id", serialization_alias="id")
    email: EmailStr
    full_name: str | None
    image_url: str | None
    phone: str | None
    role: Role

    model_config = {"from_attributes": True, "populate_by_name": True}


class TokenData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    api_key: str | None = None
    session_id: str | None = None
    user: AuthUser
