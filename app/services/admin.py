from decimal import Decimal
from typing import TypeVar
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.events import admin_event_bus
from app.core.exceptions import AppException
from app.models.domain import (
    Address,
    Brand,
    Category,
    InventoryTransaction,
    InventoryTransactionType,
    Order,
    Product,
    ProductVariant,
    Region,
    User,
    Vendor,
)
from app.schemas.admin import (
    BrandAdminInput,
    CategoryAdminInput,
    CustomerAdminData,
    CustomerRoleUpdate,
    DashboardData,
    EntityData,
    InventoryAdjustment,
    ProductAdminInput,
    RecentOrderSummary,
    RegionAdminInput,
    VendorAdminInput,
    VendorData,
)
from app.schemas.order import OrderData
from app.utils.text import slugify

EntityModel = TypeVar("EntityModel", Region, Category, Brand)


class AdminService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def dashboard(self) -> DashboardData:
        products = await self._count(Product)
        active_products = (
            await self.session.scalar(select(func.count(Product.id)).where(Product.is_active)) or 0
        )
        low_stock = (
            await self.session.scalar(
                select(func.count(ProductVariant.id)).where(
                    ProductVariant.stock_quantity <= ProductVariant.low_stock_threshold
                )
            )
            or 0
        )
        customers = (
            await self.session.scalar(select(func.count(User.id)).where(User.role == "customer"))
            or 0
        )
        orders = await self._count(Order)
        pending_orders = (
            await self.session.scalar(
                select(func.count(Order.id)).where(
                    Order.status.in_(["placed", "confirmed", "processing"])
                )
            )
            or 0
        )
        revenue = await self.session.scalar(
            select(func.coalesce(func.sum(Order.total_amount), 0)).where(
                Order.status != "cancelled"
            )
        )
        recent = await self.session.scalars(
            select(Order).order_by(Order.placed_at.desc()).limit(5)
        )
        return DashboardData(
            products=products,
            active_products=active_products,
            low_stock_variants=low_stock,
            customers=customers,
            orders=orders,
            revenue=Decimal(revenue or 0),
            pending_orders=pending_orders,
            recent_orders=[RecentOrderSummary.model_validate(item) for item in recent],
        )

    async def list_entities(self, model: type[EntityModel]) -> list[EntityData]:
        count_column = {
            Region: Product.region_id,
            Category: Product.category_id,
            Brand: Product.brand_id,
        }[model]
        rows = await self.session.execute(
            select(model, func.count(Product.id))
            .outerjoin(Product, count_column == model.id)
            .group_by(model.id)
            .order_by(model.name)
        )
        return [
            EntityData(
                int_id=item.int_id,
                name=item.name,
                is_active=item.is_active,
                product_count=count,
                subtitle=getattr(item, "subtitle", None),
            )
            for item, count in rows
        ]

    async def create_entity(
        self,
        model: type[EntityModel],
        payload: RegionAdminInput | CategoryAdminInput | BrandAdminInput,
    ) -> EntityData:
        values = payload.model_dump()
        values["slug"] = await self._unique_slug(model, payload.name)
        item = model(**values)
        self.session.add(item)
        await self.session.flush()
        await self._broadcast_dashboard()
        return EntityData(
            int_id=item.int_id,
            name=item.name,
            is_active=item.is_active,
            product_count=0,
            subtitle=getattr(item, "subtitle", None),
        )

    async def update_entity(
        self,
        model: type[EntityModel],
        item_id: int,
        payload: RegionAdminInput | CategoryAdminInput | BrandAdminInput,
    ) -> EntityData:
        item = await self._get_by_int_id(model, item_id)
        name_changed = item.name != payload.name
        for key, value in payload.model_dump().items():
            setattr(item, key, value)
        if name_changed:
            item.slug = await self._unique_slug(model, payload.name)
        await self.session.flush()
        await self._broadcast_dashboard()
        return EntityData(
            int_id=item.int_id,
            name=item.name,
            is_active=item.is_active,
            product_count=0,
            subtitle=getattr(item, "subtitle", None),
        )

    async def delete_entity(self, model: type[EntityModel], item_id: int) -> None:
        item = await self._get_by_int_id(model, item_id)
        item.is_active = False
        await self.session.flush()
        await self._broadcast_dashboard()

    async def list_products(self) -> list[Product]:
        return list(
            await self.session.scalars(
                select(Product)
                .options(
                    selectinload(Product.variants),
                    selectinload(Product.region),
                    selectinload(Product.category),
                    selectinload(Product.brand),
                    selectinload(Product.vendor),
                )
                .order_by(Product.name)
            )
        )

    async def create_product(self, payload: ProductAdminInput) -> Product:
        # Resolve int_ids to UUIDs for FK references
        region_uuid = await self._resolve_uuid(Region, payload.region_id)
        category_uuid = await self._resolve_uuid(Category, payload.category_id)
        brand_uuid = await self._resolve_uuid(Brand, payload.brand_id)
        vendor_uuid = await self._resolve_uuid(Vendor, payload.vendor_id)

        values = payload.model_dump(
            exclude={"variants", "region_id", "category_id", "brand_id", "vendor_id"}
        )
        values["region_id"] = region_uuid
        values["category_id"] = category_uuid
        values["brand_id"] = brand_uuid
        values["vendor_id"] = vendor_uuid
        product = Product(
            **values,
            slug=await self._unique_slug(Product, payload.name),
        )
        product.variants = [ProductVariant(**item.model_dump()) for item in payload.variants]
        self.session.add(product)
        await self.session.flush()
        await self._broadcast_dashboard()
        return product

    async def update_product(self, product_id: int, payload: ProductAdminInput) -> Product:
        # Resolve int_ids to UUIDs
        region_uuid = await self._resolve_uuid(Region, payload.region_id)
        category_uuid = await self._resolve_uuid(Category, payload.category_id)
        brand_uuid = await self._resolve_uuid(Brand, payload.brand_id)
        vendor_uuid = await self._resolve_uuid(Vendor, payload.vendor_id)

        product = await self.session.scalar(
            select(Product)
            .where(Product.int_id == product_id)
            .options(selectinload(Product.variants))
        )
        if not product:
            raise AppException("Product not found", status_code=404, code="product_not_found")
        values = payload.model_dump(
            exclude={"variants", "region_id", "category_id", "brand_id", "vendor_id"}
        )
        for key, value in values.items():
            setattr(product, key, value)
        product.region_id = region_uuid
        product.category_id = category_uuid
        product.brand_id = brand_uuid
        product.vendor_id = vendor_uuid
        existing = {variant.size.lower(): variant for variant in product.variants}
        for variant_input in payload.variants:
            variant = existing.get(variant_input.size.lower())
            if variant:
                for key, value in variant_input.model_dump().items():
                    setattr(variant, key, value)
            else:
                product.variants.append(ProductVariant(**variant_input.model_dump()))
        await self.session.flush()
        await self._broadcast_dashboard()
        return product

    async def deactivate_product(self, product_id: int) -> None:
        product = await self.session.scalar(select(Product).where(Product.int_id == product_id))
        if not product:
            raise AppException("Product not found", status_code=404, code="product_not_found")
        product.is_active = False
        await self.session.flush()
        await self._broadcast_dashboard()

    async def adjust_inventory(
        self,
        variant_id: int,
        payload: InventoryAdjustment,
        admin_id: UUID,
    ) -> ProductVariant:
        variant = await self.session.scalar(
            select(ProductVariant).where(ProductVariant.int_id == variant_id).with_for_update()
        )
        if not variant:
            raise AppException("Variant not found", status_code=404, code="variant_not_found")
        new_quantity = variant.stock_quantity + payload.quantity_change
        if new_quantity < 0:
            raise AppException("Inventory cannot become negative", code="negative_inventory")
        variant.stock_quantity = new_quantity
        self.session.add(
            InventoryTransaction(
                variant_id=variant.id,
                quantity_change=payload.quantity_change,
                transaction_type=InventoryTransactionType.ADJUSTMENT,
                note=payload.note,
                created_by_id=admin_id,
            )
        )
        await self.session.flush()
        await admin_event_bus.publish(
            "inventory",
            {
                "variant_id": variant.int_id,
                "stock_quantity": variant.stock_quantity,
                "product_id": variant.product_id,
            },
        )
        await self._broadcast_dashboard()
        return variant

    async def list_orders(self) -> list[OrderData]:
        orders = await self.session.scalars(
            select(Order).options(selectinload(Order.items)).order_by(Order.placed_at.desc())
        )
        return [OrderData.model_validate(item) for item in orders]

    async def update_order_status(self, order_id: int, status: object) -> OrderData:
        order = await self.session.scalar(
            select(Order).where(Order.int_id == order_id).options(selectinload(Order.items))
        )
        if not order:
            raise AppException("Order not found", status_code=404, code="order_not_found")
        order.status = status
        await self.session.flush()
        await admin_event_bus.publish(
            "order",
            {
                "order_id": order.int_id,
                "order_number": order.order_number,
                "status": str(order.status),
            },
        )
        await self._broadcast_dashboard()
        return OrderData.model_validate(order)

    async def list_customers(self) -> list[CustomerAdminData]:
        rows = await self.session.execute(
            select(
                User,
                func.count(func.distinct(Address.id)).label("addresses_count"),
                func.count(func.distinct(Order.id)).label("orders_count"),
                func.coalesce(func.sum(Order.total_amount), 0).label("total_spent"),
            )
            .outerjoin(Address, Address.user_id == User.id)
            .outerjoin(Order, Order.user_id == User.id)
            .group_by(User.id)
            .order_by(User.created_at.desc())
        )
        return [
            CustomerAdminData(
                int_id=user.int_id,
                email=user.email,
                full_name=user.full_name,
                phone=user.phone,
                image_url=user.image_url,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at,
                addresses_count=addresses_count,
                orders_count=orders_count,
                total_spent=total_spent,
            )
            for user, addresses_count, orders_count, total_spent in rows
        ]

    async def update_customer(self, user_id: int, payload: CustomerRoleUpdate) -> CustomerAdminData:
        user = await self.session.scalar(select(User).where(User.int_id == user_id))
        if not user:
            raise AppException("User not found", status_code=404, code="user_not_found")
        user.role = payload.role
        user.is_active = payload.is_active
        await self.session.flush()
        return CustomerAdminData(
            int_id=user.int_id,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            image_url=user.image_url,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
        )

    async def list_vendors(self) -> list[VendorData]:
        vendors = await self.session.scalars(select(Vendor).order_by(Vendor.name))
        return [VendorData.model_validate(vendor) for vendor in vendors]

    async def create_vendor(self, payload: VendorAdminInput) -> VendorData:
        vendor = Vendor(**payload.model_dump())
        self.session.add(vendor)
        await self.session.flush()
        return VendorData.model_validate(vendor)

    async def update_vendor(self, vendor_id: int, payload: VendorAdminInput) -> VendorData:
        vendor = await self.session.scalar(select(Vendor).where(Vendor.int_id == vendor_id))
        if not vendor:
            raise AppException("Vendor not found", status_code=404, code="vendor_not_found")
        for key, value in payload.model_dump().items():
            setattr(vendor, key, value)
        await self.session.flush()
        return VendorData.model_validate(vendor)

    async def _resolve_uuid(self, model: type, int_id: int | None):
        """Resolve an int_id to the UUID primary key for FK relationships."""
        if int_id is None:
            return None
        item = await self.session.scalar(select(model).where(model.int_id == int_id))
        if not item:
            raise AppException(
                f"Invalid {model.__tablename__} reference",
                status_code=422,
                code=f"invalid_{model.__tablename__}",
            )
        return item.id

    async def _unique_slug(self, model: type[object], name: str) -> str:
        base = slugify(name)
        exists = await self.session.scalar(select(model).where(model.slug == base))
        return f"{base}-{uuid4().hex[:8]}" if exists else base

    async def _get_by_int_id(self, model: type[EntityModel], int_id: int) -> EntityModel:
        item = await self.session.scalar(select(model).where(model.int_id == int_id))
        if not item:
            raise AppException("Record not found", status_code=404, code="record_not_found")
        return item

    async def _count(self, model: type[object]) -> int:
        return await self.session.scalar(select(func.count()).select_from(model)) or 0

    async def _broadcast_dashboard(self) -> None:
        snapshot = await self.dashboard()
        await admin_event_bus.publish(
            "dashboard",
            snapshot.model_dump(mode="json"),
        )
