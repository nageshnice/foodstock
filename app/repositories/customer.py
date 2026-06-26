from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Address


class AddressRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_user(self, user_id: UUID) -> list[Address]:
        return list(
            await self.session.scalars(
                select(Address)
                .where(Address.user_id == user_id)
                .order_by(Address.is_default.desc(), Address.created_at.desc())
            )
        )

    async def get_for_user(self, address_id: int, user_id: UUID) -> Address | None:
        return await self.session.scalar(
            select(Address).where(Address.int_id == address_id, Address.user_id == user_id)
        )

    async def clear_default(self, user_id: UUID) -> None:
        await self.session.execute(
            update(Address).where(Address.user_id == user_id).values(is_default=False)
        )
