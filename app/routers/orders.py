from fastapi import APIRouter, status

from app.core.dependencies import CurrentUser, SessionDep
from app.schemas.order import CheckoutData, CheckoutRequest, OrderData
from app.schemas.response import ApiResponse
from app.services.order import OrderService

router = APIRouter(tags=["Checkout and Orders"])


@router.post(
    "/checkout/preview",
    response_model=ApiResponse[CheckoutData],
    summary="Preview checkout bill",
    description=(
        "Calculate checkout totals for the current cart: line items, subtotal, tax, "
        "delivery fee, and grand total. Supports multiple variants of the same product. "
        "Does not place an order or change stock."
    ),
)
async def checkout_preview(
    payload: CheckoutRequest, session: SessionDep, user: CurrentUser
) -> ApiResponse[CheckoutData]:
    return ApiResponse(
        message="Checkout summary calculated",
        data=await OrderService(session).preview(user.id, payload),
    )


@router.post(
    "/orders",
    response_model=ApiResponse[OrderData],
    status_code=status.HTTP_201_CREATED,
    summary="Place order",
    description=(
        "Place an order from the current cart. Stock is checked and decremented "
        "transactionally; the cart is cleared on success. Requires minimum order amount."
    ),
)
async def place_order(
    payload: CheckoutRequest, session: SessionDep, user: CurrentUser
) -> ApiResponse[OrderData]:
    return ApiResponse(
        message="Order placed successfully",
        data=await OrderService(session).place(user.id, payload),
    )


@router.get(
    "/orders",
    response_model=ApiResponse[list[OrderData]],
    summary="List my orders",
)
async def list_orders(session: SessionDep, user: CurrentUser) -> ApiResponse[list[OrderData]]:
    return ApiResponse(message="Orders retrieved", data=await OrderService(session).list(user.id))


@router.get(
    "/orders/{order_id}",
    response_model=ApiResponse[OrderData],
    summary="Get order detail",
)
async def get_order(
    order_id: int, session: SessionDep, user: CurrentUser
) -> ApiResponse[OrderData]:
    return ApiResponse(
        message="Order retrieved", data=await OrderService(session).get(user.id, order_id)
    )
