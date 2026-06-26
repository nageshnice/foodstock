from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.models.domain import Cart, CartItem
from app.repositories.cart import CartRepository
from app.repositories.catalog import CatalogRepository
from app.schemas.cart import CartData, CartItemData

MONEY = Decimal("0.01")


class CartService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.carts = CartRepository(session)
        self.catalog = CatalogRepository(session)
        self.settings = get_settings()

    async def get(self, user_id: UUID) -> CartData:
        return self.serialize(await self.carts.get_for_user(user_id))

    async def add(self, user_id: UUID, variant_int_id: int, quantity: int) -> CartData:
        variant = await self.catalog.get_variant(variant_int_id)
        if not variant or not variant.is_active or not variant.product.is_active:
            raise AppException(
                "Product variant is unavailable", status_code=404, code="variant_unavailable"
            )
        cart = await self.carts.get_for_user(user_id)
        item = await self.carts.get_item(cart.id, variant.id)
        requested_quantity = quantity + (item.quantity if item else 0)
        if requested_quantity > variant.stock_quantity:
            raise AppException(
                "Requested quantity exceeds available stock", code="insufficient_stock"
            )
        if item:
            item.quantity = requested_quantity
        else:
            self.session.add(CartItem(cart_id=cart.id, variant_id=variant.id, quantity=quantity))
        await self.session.flush()
        return self.serialize(await self.carts.get_for_user(user_id))

    async def update(self, user_id: UUID, item_id: int, quantity: int) -> CartData:
        cart = await self.carts.get_for_user(user_id)
        item = next(
            (candidate for candidate in cart.items if candidate.variant.int_id == item_id), None
        )
        if not item:
            raise AppException("Cart item not found", status_code=404, code="cart_item_not_found")
        if quantity == 0:
            await self.carts.delete_item(item)
        elif quantity > item.variant.stock_quantity:
            raise AppException(
                "Requested quantity exceeds available stock", code="insufficient_stock"
            )
        else:
            item.quantity = quantity
            await self.session.flush()
        return self.serialize(await self.carts.get_for_user(user_id))

    async def remove(self, user_id: UUID, item_id: UUID) -> CartData:
        return await self.update(user_id, item_id, 0)

    def serialize(self, cart: Cart) -> CartData:
        items: list[CartItemData] = []
        subtotal = Decimal("0.00")
        tax_amount = Decimal("0.00")
        for item in cart.items:
            product = item.variant.product
            line_total = (item.variant.price * item.quantity).quantize(MONEY)
            subtotal += line_total
            tax_amount += line_total * product.tax_rate / Decimal("100")
            items.append(
                CartItemData(
                    id=item.variant.int_id,
                    variant_id=item.variant.int_id,
                    product_id=product.int_id,
                    product_name=product.name,
                    brand_name=product.brand.name if product.brand else None,
                    image_url=product.image_url,
                    size=item.variant.size,
                    unit_price=item.variant.price,
                    quantity=item.quantity,
                    line_total=line_total,
                )
            )
        subtotal = subtotal.quantize(MONEY)
        tax_amount = tax_amount.quantize(MONEY, rounding=ROUND_HALF_UP)
        delivery_fee = (
            Decimal("0.00")
            if subtotal >= self.settings.free_delivery_threshold
            else self.settings.delivery_fee
        )
        return CartData(
            id=cart.int_id,
            items=items,
            item_count=sum(item.quantity for item in cart.items),
            subtotal=subtotal,
            tax_amount=tax_amount,
            delivery_fee=delivery_fee,
            total_amount=(subtotal + tax_amount + delivery_fee).quantize(MONEY),
        )
