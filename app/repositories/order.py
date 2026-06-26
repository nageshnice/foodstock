from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.domain import Order


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_user(self, user_id: UUID) -> list[Order]:
        return list(
            await self.session.scalars(
                select(Order)
                .where(Order.user_id == user_id)
                .options(selectinload(Order.items))
                .order_by(Order.placed_at.desc())
            )
        )

    async def get_for_user(self, order_id: int, user_id: UUID) -> Order | None:
        return await self.session.scalar(
            select(Order)
            .where(Order.int_id == order_id, Order.user_id == user_id)
            .options(selectinload(Order.items))
        )
