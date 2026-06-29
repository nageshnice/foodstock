from fastapi import APIRouter, Depends, File, UploadFile, status

from app.core.dependencies import CurrentUser, SessionDep, require_permission
from app.core.permissions import Permission
from app.models.domain import Brand, Category, Region
from app.schemas.admin import (
    AdminAlert,
    AdminProductData,
    AdminProfileData,
    BrandAdminInput,
    CategoryAdminInput,
    CustomerAdminData,
    CustomerCreate,
    CustomerRoleUpdate,
    DashboardData,
    EntityData,
    InventoryAdjustment,
    OrderStatusUpdate,
    ProductAdminInput,
    RegionAdminInput,
    SkuSuggestionData,
    VendorAdminInput,
    VendorData,
)
from app.schemas.order import OrderData
from app.schemas.response import ApiResponse
from app.services.admin import AdminService
from app.services.uploads import save_product_image

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get(
    "/dashboard",
    response_model=ApiResponse[DashboardData],
    dependencies=[Depends(require_permission(Permission.VIEW_ADMIN))],
)
async def dashboard(session: SessionDep) -> ApiResponse[DashboardData]:
    return ApiResponse(message="Dashboard retrieved", data=await AdminService(session).dashboard())


@router.get(
    "/me",
    response_model=ApiResponse[AdminProfileData],
    dependencies=[Depends(require_permission(Permission.VIEW_ADMIN))],
)
async def admin_profile(user: CurrentUser) -> ApiResponse[AdminProfileData]:
    return ApiResponse(
        message="Profile retrieved",
        data=AdminService.profile_for(user),
    )


@router.get(
    "/alerts",
    response_model=ApiResponse[list[AdminAlert]],
    dependencies=[Depends(require_permission(Permission.VIEW_ADMIN))],
)
async def admin_alerts(session: SessionDep) -> ApiResponse[list[AdminAlert]]:
    return ApiResponse(
        message="Alerts retrieved",
        data=await AdminService(session).alerts(),
    )


@router.get(
    "/regions",
    response_model=ApiResponse[list[EntityData]],
    dependencies=[Depends(require_permission(Permission.MANAGE_CATALOG))],
)
async def admin_regions(session: SessionDep) -> ApiResponse[list[EntityData]]:
    return ApiResponse(
        message="Regions retrieved", data=await AdminService(session).list_entities(Region)
    )


@router.post(
    "/regions",
    response_model=ApiResponse[EntityData],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.MANAGE_CATALOG))],
)
async def create_region(payload: RegionAdminInput, session: SessionDep) -> ApiResponse[EntityData]:
    return ApiResponse(
        message="Region created", data=await AdminService(session).create_entity(Region, payload)
    )


@router.put(
    "/regions/{item_id}",
    response_model=ApiResponse[EntityData],
    dependencies=[Depends(require_permission(Permission.MANAGE_CATALOG))],
)
async def update_region(
    item_id: int, payload: RegionAdminInput, session: SessionDep
) -> ApiResponse[EntityData]:
    return ApiResponse(
        message="Region updated",
        data=await AdminService(session).update_entity(Region, item_id, payload),
    )


@router.delete(
    "/regions/{item_id}",
    response_model=ApiResponse[None],
    dependencies=[Depends(require_permission(Permission.MANAGE_CATALOG))],
)
async def delete_region(item_id: int, session: SessionDep) -> ApiResponse[None]:
    await AdminService(session).delete_entity(Region, item_id)
    return ApiResponse(message="Region deactivated", data=None)


@router.get(
    "/categories",
    response_model=ApiResponse[list[EntityData]],
    dependencies=[Depends(require_permission(Permission.MANAGE_CATALOG))],
)
async def admin_categories(session: SessionDep) -> ApiResponse[list[EntityData]]:
    return ApiResponse(
        message="Categories retrieved", data=await AdminService(session).list_entities(Category)
    )


@router.post(
    "/categories",
    response_model=ApiResponse[EntityData],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.MANAGE_CATALOG))],
)
async def create_category(
    payload: CategoryAdminInput, session: SessionDep
) -> ApiResponse[EntityData]:
    return ApiResponse(
        message="Category created",
        data=await AdminService(session).create_entity(Category, payload),
    )


@router.put(
    "/categories/{item_id}",
    response_model=ApiResponse[EntityData],
    dependencies=[Depends(require_permission(Permission.MANAGE_CATALOG))],
)
async def update_category(
    item_id: int, payload: CategoryAdminInput, session: SessionDep
) -> ApiResponse[EntityData]:
    return ApiResponse(
        message="Category updated",
        data=await AdminService(session).update_entity(Category, item_id, payload),
    )


@router.delete(
    "/categories/{item_id}",
    response_model=ApiResponse[None],
    dependencies=[Depends(require_permission(Permission.MANAGE_CATALOG))],
)
async def delete_category(item_id: int, session: SessionDep) -> ApiResponse[None]:
    await AdminService(session).delete_entity(Category, item_id)
    return ApiResponse(message="Category deactivated", data=None)


@router.get(
    "/brands",
    response_model=ApiResponse[list[EntityData]],
    dependencies=[Depends(require_permission(Permission.MANAGE_CATALOG))],
)
async def admin_brands(
    session: SessionDep, region_id: int | None = None
) -> ApiResponse[list[EntityData]]:
    return ApiResponse(
        message="Brands retrieved",
        data=await AdminService(session).list_entities(Brand, region_id=region_id),
    )


@router.post(
    "/brands",
    response_model=ApiResponse[EntityData],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.MANAGE_CATALOG))],
)
async def create_brand(payload: BrandAdminInput, session: SessionDep) -> ApiResponse[EntityData]:
    return ApiResponse(
        message="Brand created", data=await AdminService(session).create_entity(Brand, payload)
    )


@router.put(
    "/brands/{item_id}",
    response_model=ApiResponse[EntityData],
    dependencies=[Depends(require_permission(Permission.MANAGE_CATALOG))],
)
async def update_brand(
    item_id: int, payload: BrandAdminInput, session: SessionDep
) -> ApiResponse[EntityData]:
    return ApiResponse(
        message="Brand updated",
        data=await AdminService(session).update_entity(Brand, item_id, payload),
    )


@router.delete(
    "/brands/{item_id}",
    response_model=ApiResponse[None],
    dependencies=[Depends(require_permission(Permission.MANAGE_CATALOG))],
)
async def delete_brand(item_id: int, session: SessionDep) -> ApiResponse[None]:
    await AdminService(session).delete_entity(Brand, item_id)
    return ApiResponse(message="Brand deactivated", data=None)


@router.get(
    "/products",
    response_model=ApiResponse[list[AdminProductData]],
    dependencies=[Depends(require_permission(Permission.MANAGE_CATALOG))],
)
async def admin_products(session: SessionDep) -> ApiResponse[list[AdminProductData]]:
    products = await AdminService(session).list_products()
    return ApiResponse(
        message="Products retrieved",
        data=[_admin_product_data(item) for item in products],
    )


@router.get(
    "/products/suggest-sku",
    response_model=ApiResponse[SkuSuggestionData],
    dependencies=[Depends(require_permission(Permission.MANAGE_CATALOG))],
)
async def suggest_product_sku(
    session: SessionDep,
    region_id: int,
    category_id: int,
) -> ApiResponse[SkuSuggestionData]:
    sku, prefix = await AdminService(session).suggest_next_sku(
        region_id=region_id,
        category_id=category_id,
    )
    return ApiResponse(
        message="SKU suggestion generated",
        data=SkuSuggestionData(sku=sku, prefix=prefix),
    )


@router.post(
    "/products",
    response_model=ApiResponse[AdminProductData],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.MANAGE_CATALOG))],
)
async def create_product(
    payload: ProductAdminInput, session: SessionDep
) -> ApiResponse[AdminProductData]:
    product = await AdminService(session).create_product(payload)
    return ApiResponse(message="Product created", data=_admin_product_data(product))


@router.put(
    "/products/{product_id}",
    response_model=ApiResponse[AdminProductData],
    dependencies=[Depends(require_permission(Permission.MANAGE_CATALOG))],
)
async def update_product(
    product_id: int, payload: ProductAdminInput, session: SessionDep
) -> ApiResponse[AdminProductData]:
    product = await AdminService(session).update_product(product_id, payload)
    return ApiResponse(message="Product updated", data=_admin_product_data(product))


@router.delete(
    "/products/{product_id}",
    response_model=ApiResponse[None],
    dependencies=[Depends(require_permission(Permission.MANAGE_CATALOG))],
)
async def deactivate_product(product_id: int, session: SessionDep) -> ApiResponse[None]:
    await AdminService(session).deactivate_product(product_id)
    return ApiResponse(message="Product deactivated", data=None)


@router.post(
    "/products/upload-image",
    response_model=ApiResponse[dict[str, str]],
    dependencies=[Depends(require_permission(Permission.MANAGE_CATALOG))],
)
async def upload_product_image(
    session: SessionDep,
    file: UploadFile = File(...),
) -> ApiResponse[dict[str, str]]:
    image_url = await save_product_image(file)
    await session.commit()
    return ApiResponse(message="Image uploaded", data={"image_url": image_url})


@router.post(
    "/inventory/{variant_id}/adjust",
    response_model=ApiResponse[None],
    dependencies=[Depends(require_permission(Permission.MANAGE_INVENTORY))],
)
async def adjust_inventory(
    variant_id: int, payload: InventoryAdjustment, session: SessionDep, user: CurrentUser
) -> ApiResponse[None]:
    await AdminService(session).adjust_inventory(variant_id, payload, user.id)
    return ApiResponse(message="Inventory adjusted", data=None)


@router.get(
    "/orders",
    response_model=ApiResponse[list[OrderData]],
    dependencies=[Depends(require_permission(Permission.MANAGE_ORDERS))],
)
async def admin_orders(session: SessionDep) -> ApiResponse[list[OrderData]]:
    return ApiResponse(message="Orders retrieved", data=await AdminService(session).list_orders())


@router.patch(
    "/orders/{order_id}/status",
    response_model=ApiResponse[OrderData],
    dependencies=[Depends(require_permission(Permission.MANAGE_ORDERS))],
)
async def update_order_status(
    order_id: int, payload: OrderStatusUpdate, session: SessionDep
) -> ApiResponse[OrderData]:
    return ApiResponse(
        message="Order status updated",
        data=await AdminService(session).update_order_status(order_id, payload.status),
    )


@router.get(
    "/customers",
    response_model=ApiResponse[list[CustomerAdminData]],
    dependencies=[Depends(require_permission(Permission.MANAGE_USERS))],
)
async def admin_customers(session: SessionDep) -> ApiResponse[list[CustomerAdminData]]:
    return ApiResponse(
        message="Customers retrieved", data=await AdminService(session).list_customers()
    )


@router.post(
    "/customers",
    response_model=ApiResponse[CustomerAdminData],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.MANAGE_USERS))],
)
async def create_customer(
    payload: CustomerCreate, session: SessionDep, user: CurrentUser
) -> ApiResponse[CustomerAdminData]:
    return ApiResponse(
        message="User created",
        data=await AdminService(session).create_customer(payload, actor_role=user.role),
    )


@router.patch(
    "/customers/{user_id}",
    response_model=ApiResponse[CustomerAdminData],
    dependencies=[Depends(require_permission(Permission.MANAGE_USERS))],
)
async def update_customer(
    user_id: int, payload: CustomerRoleUpdate, session: SessionDep
) -> ApiResponse[CustomerAdminData]:
    return ApiResponse(
        message="Customer updated",
        data=await AdminService(session).update_customer(user_id, payload),
    )


@router.delete(
    "/customers/{user_id}",
    response_model=ApiResponse[None],
    dependencies=[Depends(require_permission(Permission.MANAGE_USERS))],
)
async def delete_customer(
    user_id: int, session: SessionDep, user: CurrentUser
) -> ApiResponse[None]:
    await AdminService(session).delete_customer(user_id, actor_user_id=user.id)
    await session.commit()
    return ApiResponse(message="User deleted", data=None)


@router.get(
    "/vendors",
    response_model=ApiResponse[list[VendorData]],
    dependencies=[Depends(require_permission(Permission.MANAGE_VENDORS))],
)
async def admin_vendors(session: SessionDep) -> ApiResponse[list[VendorData]]:
    return ApiResponse(message="Vendors retrieved", data=await AdminService(session).list_vendors())


@router.post(
    "/vendors",
    response_model=ApiResponse[VendorData],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.MANAGE_VENDORS))],
)
async def create_vendor(payload: VendorAdminInput, session: SessionDep) -> ApiResponse[VendorData]:
    return ApiResponse(
        message="Vendor created", data=await AdminService(session).create_vendor(payload)
    )


@router.put(
    "/vendors/{vendor_id}",
    response_model=ApiResponse[VendorData],
    dependencies=[Depends(require_permission(Permission.MANAGE_VENDORS))],
)
async def update_vendor(
    vendor_id: int, payload: VendorAdminInput, session: SessionDep
) -> ApiResponse[VendorData]:
    return ApiResponse(
        message="Vendor updated", data=await AdminService(session).update_vendor(vendor_id, payload)
    )


def _admin_product_data(product: object) -> AdminProductData:
    return AdminProductData(
        int_id=product.int_id,
        sku=product.sku,
        name=product.name,
        source_section=product.source_section,
        description=product.description,
        image_url=product.image_url,
        tax_rate=product.tax_rate,
        is_active=product.is_active,
        region_id=product.region.int_id if product.region else None,
        category_id=product.category.int_id if product.category else None,
        brand_id=product.brand.int_id if product.brand else None,
        vendor_id=product.vendor.int_id if product.vendor else None,
        region_name=product.region.name if product.region else None,
        category_name=product.category.name if product.category else None,
        brand_name=product.brand.name if product.brand else None,
        vendor_name=product.vendor.name if product.vendor else None,
        variants=product.variants,
    )
