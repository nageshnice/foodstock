from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.domain import AppSetting, ContentPage, SettingGroup, SettingValueType
from app.schemas.settings import (
    AppSettingData,
    AppSettingsBulkUpdate,
    AppSettingsGroupData,
    ContentPageAdminInput,
    ContentPageData,
)

SECRET_MASK = "••••••••"
MASK_SENTINEL = "__UNCHANGED__"

DEFAULT_SETTINGS: list[dict] = [
    {
        "setting_key": "email_enabled",
        "group": SettingGroup.EMAIL,
        "label": "Enable email notifications",
        "description": "Send transactional emails when enabled",
        "value": "false",
        "value_type": SettingValueType.BOOLEAN,
        "is_secret": False,
    },
    {
        "setting_key": "email_smtp_host",
        "group": SettingGroup.EMAIL,
        "label": "SMTP host",
        "description": "e.g. smtp.gmail.com",
        "value": "",
        "value_type": SettingValueType.STRING,
        "is_secret": False,
    },
    {
        "setting_key": "email_smtp_port",
        "group": SettingGroup.EMAIL,
        "label": "SMTP port",
        "description": "Usually 587 for TLS",
        "value": "587",
        "value_type": SettingValueType.NUMBER,
        "is_secret": False,
    },
    {
        "setting_key": "email_smtp_user",
        "group": SettingGroup.EMAIL,
        "label": "SMTP username",
        "description": "Login email or API user",
        "value": "",
        "value_type": SettingValueType.STRING,
        "is_secret": False,
    },
    {
        "setting_key": "email_smtp_password",
        "group": SettingGroup.EMAIL,
        "label": "SMTP password",
        "description": "App password or API key",
        "value": "",
        "value_type": SettingValueType.STRING,
        "is_secret": True,
    },
    {
        "setting_key": "email_from_address",
        "group": SettingGroup.EMAIL,
        "label": "From email",
        "description": "Sender address shown to customers",
        "value": "",
        "value_type": SettingValueType.STRING,
        "is_secret": False,
    },
    {
        "setting_key": "email_from_name",
        "group": SettingGroup.EMAIL,
        "label": "From name",
        "description": "Sender display name",
        "value": "Food Stock",
        "value_type": SettingValueType.STRING,
        "is_secret": False,
    },
    {
        "setting_key": "push_enabled",
        "group": SettingGroup.PUSH,
        "label": "Enable push notifications",
        "description": "Send mobile push when enabled",
        "value": "false",
        "value_type": SettingValueType.BOOLEAN,
        "is_secret": False,
    },
    {
        "setting_key": "push_fcm_server_key",
        "group": SettingGroup.PUSH,
        "label": "FCM server key",
        "description": "Firebase Cloud Messaging server key",
        "value": "",
        "value_type": SettingValueType.STRING,
        "is_secret": True,
    },
    {
        "setting_key": "push_fcm_sender_id",
        "group": SettingGroup.PUSH,
        "label": "FCM sender ID",
        "description": "Firebase project sender ID",
        "value": "",
        "value_type": SettingValueType.STRING,
        "is_secret": False,
    },
]

DEFAULT_PAGES: list[dict] = [
    {
        "slug": "terms-and-conditions",
        "title": "Terms & Conditions",
        "body": "<p>Update your terms and conditions content from Admin → Settings.</p>",
    },
    {
        "slug": "privacy-policy",
        "title": "Privacy Policy",
        "body": "<p>Update your privacy policy content from Admin → Settings.</p>",
    },
    {
        "slug": "contact-us",
        "title": "Contact Us",
        "body": "<p>Reach out to our support team for order and account help.</p>",
    },
]


class SettingsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def ensure_defaults(self) -> None:
        existing_keys = set(
            await self.session.scalars(select(AppSetting.setting_key))
        )
        for item in DEFAULT_SETTINGS:
            if item["setting_key"] in existing_keys:
                continue
            self.session.add(AppSetting(id=uuid4(), **item))
        existing_slugs = set(await self.session.scalars(select(ContentPage.slug)))
        for item in DEFAULT_PAGES:
            if item["slug"] in existing_slugs:
                continue
            self.session.add(ContentPage(id=uuid4(), **item))
        await self.session.flush()

    async def list_settings_groups(self) -> list[AppSettingsGroupData]:
        await self.ensure_defaults()
        settings = list(
            await self.session.scalars(select(AppSetting).order_by(AppSetting.int_id))
        )
        grouped: dict[SettingGroup, list[AppSettingData]] = {g: [] for g in SettingGroup}
        for row in settings:
            grouped[row.group].append(self._to_setting_data(row, mask_secrets=True))
        return [
            AppSettingsGroupData(
                group=group,
                enabled=self._group_enabled(grouped[group]),
                settings=grouped[group],
            )
            for group in SettingGroup
        ]

    async def update_settings(self, payload: AppSettingsBulkUpdate) -> list[AppSettingsGroupData]:
        await self.ensure_defaults()
        by_id = {
            row.int_id: row
            for row in await self.session.scalars(select(AppSetting))
        }
        for item in payload.items:
            row = by_id.get(item.id)
            if not row:
                raise AppException(
                    f"Setting {item.id} not found",
                    status_code=404,
                    code="setting_not_found",
                )
            if item.is_active is not None:
                row.is_active = item.is_active
            if item.value is not None:
                if row.is_secret and item.value in (SECRET_MASK, MASK_SENTINEL, ""):
                    pass
                else:
                    row.value = item.value
        await self.session.flush()
        return await self.list_settings_groups()

    async def list_content_pages(self) -> list[ContentPageData]:
        await self.ensure_defaults()
        pages = await self.session.scalars(select(ContentPage).order_by(ContentPage.slug))
        return [ContentPageData.model_validate(page) for page in pages]

    async def update_content_page(self, slug: str, payload: ContentPageAdminInput) -> ContentPageData:
        await self.ensure_defaults()
        page = await self.session.scalar(select(ContentPage).where(ContentPage.slug == slug))
        if not page:
            raise AppException("Page not found", status_code=404, code="content_not_found")
        page.title = payload.title
        page.body = payload.body
        page.is_active = payload.is_active
        page.contact_email = payload.contact_email
        page.contact_phone = payload.contact_phone
        page.contact_address = payload.contact_address
        page.support_hours = payload.support_hours
        await self.session.flush()
        return ContentPageData.model_validate(page)

    async def get_public_content(self, slug: str) -> ContentPageData:
        await self.ensure_defaults()
        page = await self.session.scalar(
            select(ContentPage).where(ContentPage.slug == slug, ContentPage.is_active.is_(True))
        )
        if not page:
            raise AppException("Page not found", status_code=404, code="content_not_found")
        return ContentPageData.model_validate(page)

    @staticmethod
    def _group_enabled(settings: list[AppSettingData]) -> bool:
        for item in settings:
            if item.setting_key.endswith("_enabled"):
                return (item.value or "false").lower() == "true" and item.is_active
        return False

    @staticmethod
    def _to_setting_data(row: AppSetting, *, mask_secrets: bool) -> AppSettingData:
        has_value = bool(row.value)
        value = row.value
        if mask_secrets and row.is_secret and has_value:
            value = SECRET_MASK
        return AppSettingData(
            int_id=row.int_id,
            setting_key=row.setting_key,
            group=row.group,
            label=row.label,
            description=row.description,
            value=value,
            value_type=row.value_type,
            is_active=row.is_active,
            is_secret=row.is_secret,
            has_value=has_value,
        )
