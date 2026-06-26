from fastapi import APIRouter, status

from app.core.dependencies import CurrentUser, SessionDep
from app.schemas.order import CheckoutData, CheckoutRequest, OrderData
from app.schemas.response import ApiResponse
from app.services.order import OrderService

router = APIRouter(tags=["Checkout and Orders"])


@router.post("/checkout/preview", response_model=ApiResponse[CheckoutData])
async def checkout_preview(
    payload: CheckoutRequest, session: SessionDep, user: CurrentUser
) -> ApiResponse[CheckoutData]:
    return ApiResponse(
        message="Checkout summary calculated",
        data=await OrderService(session).preview(user.id, payload),
    )


@router.post("/orders", response_model=ApiResponse[OrderData], status_code=status.HTTP_201_CREATED)
async def place_order(
    payload: CheckoutRequest, session: SessionDep, user: CurrentUser
) -> ApiResponse[OrderData]:
    return ApiResponse(
        message="Order placed successfully",
        data=await OrderService(session).place(user.id, payload),
    )


@router.get("/orders", response_model=ApiResponse[list[OrderData]])
async def list_orders(session: SessionDep, user: CurrentUser) -> ApiResponse[list[OrderData]]:
    return ApiResponse(message="Orders retrieved", data=await OrderService(session).list(user.id))


@router.get("/orders/{order_id}", response_model=ApiResponse[OrderData])
async def get_order(
    order_id: int, session: SessionDep, user: CurrentUser
) -> ApiResponse[OrderData]:
    return ApiResponse(
        message="Order retrieved", data=await OrderService(session).get(user.id, order_id)
    )
