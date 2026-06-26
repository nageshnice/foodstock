from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.domain import Address, User
from app.repositories.customer import AddressRepository
from app.schemas.customer import AddressData, AddressInput, ProfileData, ProfileUpdate


class CustomerService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.addresses = AddressRepository(session)

    async def update_profile(self, user: User, payload: ProfileUpdate) -> ProfileData:
        user.full_name = payload.full_name
        user.phone = payload.phone
        user.image_url = payload.image_url
        await self.session.flush()
        return ProfileData.model_validate(user)

    async def list_addresses(self, user_id: UUID) -> list[AddressData]:
        return [
            AddressData.model_validate(item) for item in await self.addresses.list_for_user(user_id)
        ]

    async def add_address(self, user_id: UUID, payload: AddressInput) -> AddressData:
        existing = await self.addresses.list_for_user(user_id)
        values = payload.model_dump()
        values["is_default"] = payload.is_default or not existing
        if values["is_default"]:
            await self.addresses.clear_default(user_id)
        address = Address(user_id=user_id, **values)
        self.session.add(address)
        await self.session.flush()
        return AddressData.model_validate(address)

    async def update_address(
        self, user_id: UUID, address_id: int, payload: AddressInput
    ) -> AddressData:
        address = await self._get_address(user_id, address_id)
        if payload.is_default:
            await self.addresses.clear_default(user_id)
        for key, value in payload.model_dump().items():
            setattr(address, key, value)
        await self.session.flush()
        return AddressData.model_validate(address)

    async def set_default(self, user_id: UUID, address_id: int) -> AddressData:
        address = await self._get_address(user_id, address_id)
        await self.addresses.clear_default(user_id)
        address.is_default = True
        await self.session.flush()
        return AddressData.model_validate(address)

    async def delete_address(self, user_id: UUID, address_id: int) -> None:
        address = await self._get_address(user_id, address_id)
        await self.session.delete(address)
        await self.session.flush()

    async def _get_address(self, user_id: UUID, address_id: int) -> Address:
        address = await self.addresses.get_for_user(address_id, user_id)
        if not address:
            raise AppException("Address not found", status_code=404, code="address_not_found")
        return address
