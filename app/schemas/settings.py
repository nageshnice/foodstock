from datetime import datetime

from pydantic import BaseModel, Field

from app.models.domain import SettingGroup, SettingValueType


class AppSettingData(BaseModel):
    id: int = Field(validation_alias="int_id", serialization_alias="id")
    setting_key: str
    group: SettingGroup
    label: str
    description: str | None = None
    value: str | None = None
    value_type: SettingValueType
    is_active: bool
    is_secret: bool
    has_value: bool = False

    model_config = {"populate_by_name": True}


class AppSettingUpdate(BaseModel):
    id: int
    value: str | None = None
    is_active: bool | None = None


class AppSettingsBulkUpdate(BaseModel):
    items: list[AppSettingUpdate] = Field(min_length=1)


class AppSettingsGroupData(BaseModel):
    group: SettingGroup
    enabled: bool
    settings: list[AppSettingData]


class ContentPageData(BaseModel):
    slug: str
    title: str
    body: str
    is_active: bool
    contact_email: str | None = None
    contact_phone: str | None = None
    contact_address: str | None = None
    support_hours: str | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class ContentPageAdminInput(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    body: str = ""
    is_active: bool = True
    contact_email: str | None = None
    contact_phone: str | None = None
    contact_address: str | None = None
    support_hours: str | None = None
