from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.domain import Brand, Cart, CartItem, Product, ProductVariant


def _cart_load_options():
    return (
        selectinload(Cart.items)
        .selectinload(CartItem.variant)
        .selectinload(ProductVariant.product)
        .selectinload(Product.brand)
    )


class CartRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _load_cart(self, cart_id: UUID) -> Cart:
        cart = await self.session.scalar(
            select(Cart).where(Cart.id == cart_id).options(_cart_load_options())
        )
        if not cart:
            raise RuntimeError("Cart not found after save")
        return cart

    async def get_for_user(self, user_id: UUID) -> Cart:
        cart = await self.session.scalar(
            select(Cart).where(Cart.user_id == user_id).options(_cart_load_options())
        )
        if cart:
            return cart
        cart = Cart(user_id=user_id)
        self.session.add(cart)
        await self.session.flush()
        return await self._load_cart(cart.id)

    async def get_item(self, cart_id: UUID, variant_id: UUID) -> CartItem | None:
        return await self.session.scalar(
            select(CartItem).where(CartItem.cart_id == cart_id, CartItem.variant_id == variant_id)
        )

    async def get_item_with_details(self, cart_id: UUID, variant_id: UUID) -> CartItem | None:
        return await self.session.scalar(
            select(CartItem)
            .where(CartItem.cart_id == cart_id, CartItem.variant_id == variant_id)
            .options(
                selectinload(CartItem.variant)
                .selectinload(ProductVariant.product)
                .selectinload(Product.brand)
            )
        )

    async def delete_item(self, item: CartItem) -> None:
        await self.session.delete(item)
        await self.session.flush()

    async def clear(self, cart_id: UUID) -> None:
        await self.session.execute(delete(CartItem).where(CartItem.cart_id == cart_id))
        await self.session.flush()
