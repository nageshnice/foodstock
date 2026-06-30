from decimal import Decimal
from datetime import datetime, timedelta, timezone
from typing import TypeVar
from uuid import UUID, uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.events import admin_event_bus
from app.core.exceptions import AppException
from app.core.permissions import Role
from app.core.security import hash_password
from app.models.domain import (
    Address,
    Brand,
    Cart,
    CartItem,
    Category,
    InventoryTransaction,
    InventoryTransactionType,
    Order,
    OrderItem,
    OrderStatus,
    Product,
    ProductVariant,
    Region,
    User,
    UserApiKey,
    UserLoginSession,
    Vendor,
)
from app.schemas.admin import (
    AdminAlert,
    AdminProfileData,
    BrandAdminInput,
    CategoryAdminInput,
    CustomerAdminData,
    CustomerCreate,
    CustomerRoleUpdate,
    DailySalesPoint,
    DashboardData,
    EntityData,
    InventoryAdjustment,
    ProductAdminInput,
    RecentOrderSummary,
    RegionAdminInput,
    StatusBreakdown,
    TopProductSummary,
    VendorAdminInput,
    VendorData,
)
from app.schemas.order import OrderData
from app.services.order import OrderService
from app.utils.sku import build_sku_prefix, next_sku_from_existing
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
                Order.status != OrderStatus.CANCELLED
            )
        )
        revenue = Decimal(revenue or 0)

        fulfilled_orders = (
            await self.session.scalar(
                select(func.count(Order.id)).where(Order.status != OrderStatus.CANCELLED)
            )
            or 0
        )
        avg_order_value = (
            (revenue / fulfilled_orders).quantize(Decimal("0.01"))
            if fulfilled_orders
            else Decimal("0.00")
        )

        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_orders = (
            await self.session.scalar(
                select(func.count(Order.id)).where(Order.placed_at >= today_start)
            )
            or 0
        )
        today_revenue = Decimal(
            await self.session.scalar(
                select(func.coalesce(func.sum(Order.total_amount), 0)).where(
                    Order.placed_at >= today_start,
                    Order.status != OrderStatus.CANCELLED,
                )
            )
            or 0
        )

        trend_start = today_start - timedelta(days=6)
        trend_rows = (
            await self.session.execute(
                select(
                    func.date(Order.placed_at).label("day"),
                    func.count(Order.id),
                    func.coalesce(func.sum(Order.total_amount), 0),
                )
                .where(
                    Order.placed_at >= trend_start,
                    Order.status != OrderStatus.CANCELLED,
                )
                .group_by(func.date(Order.placed_at))
            )
        ).all()
        trend_map = {
            (row.day.isoformat() if hasattr(row.day, "isoformat") else str(row.day)): (
                row[1],
                Decimal(row[2] or 0),
            )
            for row in trend_rows
        }
        sales_trend = [
            DailySalesPoint(
                date=day.isoformat(),
                orders=trend_map.get(day.isoformat(), (0, Decimal("0")))[0],
                revenue=trend_map.get(day.isoformat(), (0, Decimal("0")))[1],
            )
            for day in ((trend_start + timedelta(days=offset)).date() for offset in range(7))
        ]

        status_rows = (
            await self.session.execute(
                select(Order.status, func.count(Order.id)).group_by(Order.status)
            )
        ).all()
        orders_by_status = [
            StatusBreakdown(status=status, count=count) for status, count in status_rows
        ]

        top_rows = (
            await self.session.execute(
                select(
                    OrderItem.product_name,
                    func.sum(OrderItem.quantity),
                    func.coalesce(func.sum(OrderItem.line_total), 0),
                )
                .join(Order, Order.id == OrderItem.order_id)
                .where(Order.status != OrderStatus.CANCELLED)
                .group_by(OrderItem.product_name)
                .order_by(func.sum(OrderItem.quantity).desc())
                .limit(5)
            )
        ).all()
        top_products = [
            TopProductSummary(
                name=name,
                quantity=int(quantity or 0),
                revenue=Decimal(revenue_total or 0),
            )
            for name, quantity, revenue_total in top_rows
        ]

        recent = await self.session.scalars(
            select(Order).order_by(Order.placed_at.desc()).limit(8)
        )
        return DashboardData(
            products=products,
            active_products=active_products,
            low_stock_variants=low_stock,
            customers=customers,
            orders=orders,
            revenue=revenue,
            pending_orders=pending_orders,
            today_orders=today_orders,
            today_revenue=today_revenue,
            avg_order_value=avg_order_value,
            sales_trend=sales_trend,
            orders_by_status=orders_by_status,
            top_products=top_products,
            recent_orders=[RecentOrderSummary.model_validate(item) for item in recent],
        )

    @staticmethod
    def profile_for(user: User) -> AdminProfileData:
        return AdminProfileData.model_validate(user)

    async def alerts(self) -> list[AdminAlert]:
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
        pending_orders = (
            await self.session.scalar(
                select(func.count(Order.id)).where(
                    Order.status.in_(["placed", "confirmed", "processing"])
                )
            )
            or 0
        )
        placed_today = (
            await self.session.scalar(
                select(func.count(Order.id)).where(
                    Order.status == OrderStatus.PLACED,
                    func.date(Order.placed_at) == func.curdate(),
                )
            )
            or 0
        )

        alerts: list[AdminAlert] = []
        if low_stock > 0:
            alerts.append(
                AdminAlert(
                    id="low_stock",
                    severity="warning",
                    title="Low stock alert",
                    message=f"{low_stock} product variant{'s' if low_stock != 1 else ''} below threshold",
                    href="/inventory",
                )
            )
        if pending_orders > 0:
            alerts.append(
                AdminAlert(
                    id="pending_orders",
                    severity="info",
                    title="Pending fulfilment",
                    message=f"{pending_orders} order{'s' if pending_orders != 1 else ''} need attention",
                    href="/orders",
                )
            )
        inactive_products = max(products - active_products, 0)
        if inactive_products > 0:
            alerts.append(
                AdminAlert(
                    id="inactive_products",
                    severity="info",
                    title="Inactive catalog items",
                    message=f"{inactive_products} product{'s' if inactive_products != 1 else ''} not live in store",
                    href="/products",
                )
            )
        if placed_today > 0:
            alerts.append(
                AdminAlert(
                    id="new_orders_today",
                    severity="success",
                    title="New orders today",
                    message=f"{placed_today} new order{'s' if placed_today != 1 else ''} placed today",
                    href="/orders",
                )
            )
        return alerts

    @staticmethod
    def _entity_data(item: Region | Category | Brand, product_count: int = 0) -> EntityData:
        region_id = None
        region_name = None
        if isinstance(item, Brand) and item.region is not None:
            region_id = item.region.int_id
            region_name = item.region.name
        return EntityData(
            int_id=item.int_id,
            name=item.name,
            is_active=item.is_active,
            product_count=product_count,
            subtitle=getattr(item, "subtitle", None),
            description=getattr(item, "description", None),
            image_url=getattr(item, "image_url", None),
            logo_url=getattr(item, "logo_url", None),
            display_order=getattr(item, "display_order", None),
            region_id=region_id,
            region_name=region_name,
        )

    async def list_entities(
        self, model: type[EntityModel], *, region_id: int | None = None
    ) -> list[EntityData]:
        count_column = {
            Region: Product.region_id,
            Category: Product.category_id,
            Brand: Product.brand_id,
        }[model]
        statement = (
            select(model, func.count(Product.id))
            .outerjoin(Product, count_column == model.id)
            .group_by(model.id)
            .order_by(model.name)
        )
        if model is Brand:
            statement = statement.options(selectinload(Brand.region))
            if region_id is not None:
                region_sub = (
                    select(Region.id).where(Region.int_id == region_id).scalar_subquery()
                )
                statement = statement.where(Brand.region_id == region_sub)
        rows = await self.session.execute(statement)
        return [self._entity_data(item, count) for item, count in rows]

    async def create_entity(
        self,
        model: type[EntityModel],
        payload: RegionAdminInput | CategoryAdminInput | BrandAdminInput,
    ) -> EntityData:
        values = payload.model_dump(exclude={"region_id"} if model is Brand else set())
        values["slug"] = await self._unique_slug(model, payload.name)
        if model is Brand:
            brand_payload = payload
            if not isinstance(brand_payload, BrandAdminInput):
                raise AppException("Invalid brand payload", status_code=422, code="invalid_brand")
            values["region_id"] = await self._resolve_uuid(Region, brand_payload.region_id)
        item = model(**values)
        self.session.add(item)
        await self.session.flush()
        if model is Brand:
            await self.session.refresh(item, attribute_names=["region"])
            region = await self.session.scalar(
                select(Region).where(Region.id == item.region_id)
            )
            item.region = region
        await self._broadcast_dashboard()
        return self._entity_data(item, product_count=0)

    async def update_entity(
        self,
        model: type[EntityModel],
        item_id: int,
        payload: RegionAdminInput | CategoryAdminInput | BrandAdminInput,
    ) -> EntityData:
        item = await self._get_by_int_id(model, item_id)
        name_changed = item.name != payload.name
        payload_data = payload.model_dump(exclude={"region_id"} if model is Brand else set())
        for key, value in payload_data.items():
            setattr(item, key, value)
        if model is Brand and isinstance(payload, BrandAdminInput):
            item.region_id = await self._resolve_uuid(Region, payload.region_id)
        if name_changed:
            item.slug = await self._unique_slug(model, payload.name)
        await self.session.flush()
        if model is Brand:
            region = await self.session.scalar(select(Region).where(Region.id == item.region_id))
            item.region = region
        await self._broadcast_dashboard()
        return self._entity_data(item, product_count=0)

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

    async def suggest_next_sku(self, *, region_id: int, category_id: int) -> tuple[str, str]:
        region = await self._get_by_int_id(Region, region_id)
        category = await self._get_by_int_id(Category, category_id)
        prefix = build_sku_prefix(region.name, category.name)
        existing = list(
            await self.session.scalars(
                select(Product.sku).where(Product.sku.ilike(f"{prefix}-%"))
            )
        )
        return next_sku_from_existing(prefix, existing), prefix

    async def create_product(self, payload: ProductAdminInput) -> Product:
        region_uuid = await self._resolve_uuid(Region, payload.region_id)
        category_uuid = await self._resolve_uuid(Category, payload.category_id)
        brand_uuid = await self._resolve_uuid(Brand, payload.brand_id)
        vendor_uuid = await self._resolve_uuid(Vendor, payload.vendor_id)

        if brand_uuid and region_uuid:
            brand = await self.session.scalar(select(Brand).where(Brand.id == brand_uuid))
            if brand and brand.region_id and brand.region_id != region_uuid:
                raise AppException(
                    "Selected brand does not belong to the chosen region",
                    status_code=422,
                    code="brand_region_mismatch",
                )

        sku = (payload.sku or "").strip()
        if not sku:
            if payload.region_id is None or payload.category_id is None:
                raise AppException(
                    "Region and category are required to generate a SKU",
                    status_code=422,
                    code="sku_generation_failed",
                )
            sku, _ = await self.suggest_next_sku(
                region_id=payload.region_id,
                category_id=payload.category_id,
            )

        existing_sku = await self.session.scalar(select(Product.id).where(Product.sku == sku))
        if existing_sku:
            raise AppException(
                "A product with this SKU already exists",
                status_code=409,
                code="duplicate_sku",
            )

        values = payload.model_dump(
            exclude={"variants", "region_id", "category_id", "brand_id", "vendor_id", "sku"}
        )
        values["sku"] = sku
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
        return await self._load_admin_product(product.id)

    async def update_product(self, product_id: int, payload: ProductAdminInput) -> Product:
        region_uuid = await self._resolve_uuid(Region, payload.region_id)
        category_uuid = await self._resolve_uuid(Category, payload.category_id)
        brand_uuid = await self._resolve_uuid(Brand, payload.brand_id)
        vendor_uuid = await self._resolve_uuid(Vendor, payload.vendor_id)

        if brand_uuid and region_uuid:
            brand = await self.session.scalar(select(Brand).where(Brand.id == brand_uuid))
            if brand and brand.region_id and brand.region_id != region_uuid:
                raise AppException(
                    "Selected brand does not belong to the chosen region",
                    status_code=422,
                    code="brand_region_mismatch",
                )

        product = await self.session.scalar(
            select(Product)
            .where(Product.int_id == product_id)
            .options(selectinload(Product.variants))
        )
        if not product:
            raise AppException("Product not found", status_code=404, code="product_not_found")

        sku = (payload.sku or "").strip() or product.sku
        if sku != product.sku:
            existing_sku = await self.session.scalar(
                select(Product.id).where(Product.sku == sku, Product.id != product.id)
            )
            if existing_sku:
                raise AppException(
                    "A product with this SKU already exists",
                    status_code=409,
                    code="duplicate_sku",
                )

        values = payload.model_dump(
            exclude={"variants", "region_id", "category_id", "brand_id", "vendor_id", "sku"}
        )
        values["sku"] = sku
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
        return await self._load_admin_product(product.id)

    async def _load_admin_product(self, product_id: UUID) -> Product:
        product = await self.session.scalar(
            select(Product)
            .where(Product.id == product_id)
            .options(
                selectinload(Product.variants),
                selectinload(Product.region),
                selectinload(Product.category),
                selectinload(Product.brand),
                selectinload(Product.vendor),
            )
        )
        if not product:
            raise AppException("Product not found", status_code=404, code="product_not_found")
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
            select(ProductVariant)
            .where(ProductVariant.int_id == variant_id)
            .options(selectinload(ProductVariant.product))
            .with_for_update()
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
                "product_id": variant.product.int_id,
            },
        )
        await self._broadcast_dashboard()
        return variant

    async def list_orders(self) -> list[OrderData]:
        orders = await self.session.scalars(
            select(Order).options(selectinload(Order.items)).order_by(Order.placed_at.desc())
        )
        serializer = OrderService(self.session)
        return [serializer._to_order_data(item) for item in orders]

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
        return OrderService(self.session)._to_order_data(order)

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

    async def create_customer(
        self, payload: CustomerCreate, actor_role: Role
    ) -> CustomerAdminData:
        if payload.role == Role.SUPER_ADMIN and actor_role != Role.SUPER_ADMIN:
            raise AppException(
                "Only super admins can create super admin accounts",
                status_code=403,
                code="role_forbidden",
            )

        email = str(payload.email).lower()
        if await self.session.scalar(select(User).where(User.email == email)):
            raise AppException(
                "An account with this email already exists",
                status_code=409,
                code="email_exists",
            )

        if payload.phone:
            if await self.session.scalar(select(User).where(User.phone == payload.phone)):
                raise AppException(
                    "Phone number already in use",
                    status_code=409,
                    code="phone_exists",
                )

        user = User(
            email=email,
            password_hash=hash_password(payload.password),
            full_name=payload.full_name,
            phone=payload.phone,
            role=payload.role,
            is_active=payload.is_active,
        )
        self.session.add(user)
        await self.session.flush()
        self.session.add(Cart(user_id=user.id))
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

    async def delete_customer(self, user_id: int, actor_user_id: UUID | None = None) -> None:
        user = await self.session.scalar(select(User).where(User.int_id == user_id))
        if not user:
            raise AppException("User not found", status_code=404, code="user_not_found")
        if user.role == Role.SUPER_ADMIN:
            raise AppException(
                "Super admin accounts cannot be deleted",
                status_code=403,
                code="protected_user",
            )
        if actor_user_id and user.id == actor_user_id:
            raise AppException(
                "You cannot delete your own account",
                status_code=403,
                code="self_delete_forbidden",
            )

        order_count = (
            await self.session.scalar(
                select(func.count()).select_from(Order).where(Order.user_id == user.id)
            )
            or 0
        )
        if order_count > 0:
            raise AppException(
                "Cannot delete a user with order history. Suspend the account instead.",
                status_code=409,
                code="user_has_orders",
            )

        await self.session.execute(delete(UserApiKey).where(UserApiKey.user_id == user.id))
        await self.session.execute(
            delete(UserLoginSession).where(UserLoginSession.user_id == user.id)
        )

        cart = await self.session.scalar(select(Cart).where(Cart.user_id == user.id))
        if cart:
            await self.session.execute(delete(CartItem).where(CartItem.cart_id == cart.id))
            await self.session.delete(cart)

        await self.session.execute(delete(Address).where(Address.user_id == user.id))
        await self.session.delete(user)
        await self.session.flush()

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
