from fastapi import APIRouter, status

from app.core.dependencies import CurrentUser, SessionDep
from app.schemas.cart import CartData, CartItemData, CartItemInput, CartItemUpdate
from app.schemas.response import ApiResponse
from app.services.cart import CartService

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.get("", response_model=ApiResponse[CartData])
async def get_cart(session: SessionDep, user: CurrentUser) -> ApiResponse[CartData]:
    return ApiResponse(message="Cart retrieved", data=await CartService(session).get(user.id))


@router.delete("", response_model=ApiResponse[CartData])
async def clear_cart(session: SessionDep, user: CurrentUser) -> ApiResponse[CartData]:
    return ApiResponse(message="Cart cleared", data=await CartService(session).clear(user.id))


@router.post("/items", response_model=ApiResponse[CartItemData], status_code=status.HTTP_201_CREATED)
async def add_cart_item(
    payload: CartItemInput, session: SessionDep, user: CurrentUser
) -> ApiResponse[CartItemData]:
    data = await CartService(session).add(
        user.id, payload.variant_id, payload.quantity, replace=payload.replace
    )
    return ApiResponse(message="Item added to cart", data=data)


@router.patch("/items/{item_id}", response_model=ApiResponse[CartData])
async def update_cart_item(
    item_id: int,
    payload: CartItemUpdate,
    session: SessionDep,
    user: CurrentUser,
) -> ApiResponse[CartData]:
    data = await CartService(session).update(user.id, item_id, payload.quantity)
    return ApiResponse(message="Cart updated", data=data)


@router.delete("/items/{item_id}", response_model=ApiResponse[CartData])
async def delete_cart_item(
    item_id: int, session: SessionDep, user: CurrentUser
) -> ApiResponse[CartData]:
    return ApiResponse(
        message="Item removed", data=await CartService(session).remove(user.id, item_id)
    )
