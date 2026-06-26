from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.domain import Cart, CartItem, Product, ProductVariant


class CartRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_for_user(self, user_id: UUID) -> Cart:
        statement = (
            select(Cart)
            .where(Cart.user_id == user_id)
            .options(
                selectinload(Cart.items)
                .selectinload(CartItem.variant)
                .selectinload(ProductVariant.product)
                .selectinload(Product.brand)
            )
        )
        cart = await self.session.scalar(statement)
        if cart:
            return cart
        cart = Cart(user_id=user_id)
        self.session.add(cart)
        await self.session.flush()
        return cart

    async def get_item(self, cart_id: UUID, variant_id: UUID) -> CartItem | None:
        return await self.session.scalar(
            select(CartItem).where(CartItem.cart_id == cart_id, CartItem.variant_id == variant_id)
        )

    async def delete_item(self, item: CartItem) -> None:
        await self.session.delete(item)
        await self.session.flush()

    async def clear(self, cart_id: UUID) -> None:
        await self.session.execute(delete(CartItem).where(CartItem.cart_id == cart_id))
        await self.session.flush()
