from datetime import UTC, datetime
from decimal import Decimal
from secrets import randbelow
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.models.domain import (
    Address,
    InventoryTransaction,
    InventoryTransactionType,
    Order,
    OrderItem,
)
from app.repositories.cart import CartRepository
from app.repositories.catalog import CatalogRepository
from app.repositories.customer import AddressRepository
from app.repositories.order import OrderRepository
from app.schemas.customer import AddressData
from app.schemas.order import CheckoutBillSummary, CheckoutData, CheckoutRequest, OrderData
from app.services.cart import CartService


class OrderService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings = get_settings()
        self.carts = CartRepository(session)
        self.cart_service = CartService(session)
        self.catalog = CatalogRepository(session)
        self.addresses = AddressRepository(session)
        self.orders = OrderRepository(session)

    async def preview(self, user_id: UUID, payload: CheckoutRequest) -> CheckoutData:
        cart_data = await self.cart_service.get(user_id)
        if not cart_data.items:
            raise AppException("Cart is empty", code="empty_cart")
        address = await self.addresses.get_for_user(payload.address_id, user_id)
        if not address:
            raise AppException("Address not found", status_code=404, code="address_not_found")
        return CheckoutData(
            cart=cart_data,
            address=AddressData.model_validate(address),
            payment_method=payload.payment_method,
            minimum_order_met=cart_data.subtotal >= self.settings.minimum_order_amount,
            bill_summary=CheckoutBillSummary(
                item_count=cart_data.item_count,
                line_count=len(cart_data.items),
                subtotal=cart_data.subtotal,
                delivery_fee=cart_data.delivery_fee,
                tax_amount=cart_data.tax_amount,
                total_amount=cart_data.total_amount,
                minimum_order_amount=self.settings.minimum_order_amount,
                minimum_order_met=cart_data.subtotal >= self.settings.minimum_order_amount,
                free_delivery_threshold=self.settings.free_delivery_threshold,
            ),
        )

    async def place(self, user_id: UUID, payload: CheckoutRequest) -> OrderData:
        preview = await self.preview(user_id, payload)
        if not preview.minimum_order_met:
            raise AppException(
                f"Minimum order amount is {self.settings.minimum_order_amount}",
                code="minimum_order_not_met",
            )
        cart = await self.carts.get_for_user(user_id)
        address = await self.addresses.get_for_user(payload.address_id, user_id)
        if not address:
            raise AppException("Address not found", status_code=404, code="address_not_found")

        locked_variants = {}
        for item in cart.items:
            variant = await self.catalog.get_variant(item.variant.int_id, for_update=True)
            if not variant or variant.stock_quantity < item.quantity:
                raise AppException(
                    f"Insufficient stock for {item.variant.product.name}", code="insufficient_stock"
                )
            locked_variants[item.variant_id] = variant

        cart_data = self.cart_service.serialize(cart)
        order = Order(
            order_number=f"ORD{randbelow(1_000_000):06d}",
            user_id=user_id,
            address_id=address.id,
            payment_method=payload.payment_method,
            subtotal=cart_data.subtotal,
            tax_amount=cart_data.tax_amount,
            delivery_fee=cart_data.delivery_fee,
            discount_amount=Decimal("0.00"),
            total_amount=cart_data.total_amount,
            delivery_address=self._format_address(address),
            placed_at=datetime.now(UTC),
        )
        self.session.add(order)
        await self.session.flush()
        for item in cart.items:
            variant = locked_variants[item.variant_id]
            product = variant.product
            line_total = variant.price * item.quantity
            variant.stock_quantity -= item.quantity
            self.session.add(
                OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    variant_id=variant.id,
                    product_name=product.name,
                    variant_size=variant.size,
                    unit_price=variant.price,
                    quantity=item.quantity,
                    tax_rate=product.tax_rate,
                    line_total=line_total,
                )
            )
            self.session.add(
                InventoryTransaction(
                    variant_id=variant.id,
                    quantity_change=-item.quantity,
                    transaction_type=InventoryTransactionType.SALE,
                    note=f"Order {order.order_number}",
                    created_by_id=user_id,
                )
            )
        await self.carts.clear(cart.id)
        await self.session.flush()
        saved = await self.orders.get_for_user(order.int_id, user_id)
        if not saved:
            raise RuntimeError("Order was not persisted")
        return OrderData.model_validate(saved)

    async def list(self, user_id: UUID) -> list[OrderData]:
        return [OrderData.model_validate(item) for item in await self.orders.list_for_user(user_id)]

    async def get(self, user_id: UUID, order_id: int) -> OrderData:
        order = await self.orders.get_for_user(order_id, user_id)
        if not order:
            raise AppException("Order not found", status_code=404, code="order_not_found")
        return OrderData.model_validate(order)

    @staticmethod
    def _format_address(address: Address) -> str:
        parts = [
            address.house_flat_floor,
            address.building_street,
            address.area_locality,
            address.city,
            address.state,
            address.pincode,
        ]
        return ", ".join(str(part) for part in parts if part)
