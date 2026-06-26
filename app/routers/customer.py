from fastapi import APIRouter, status

from app.core.dependencies import CurrentUser, SessionDep
from app.schemas.customer import AddressData, AddressInput, ProfileData, ProfileUpdate
from app.schemas.response import ApiResponse
from app.services.customer import CustomerService

router = APIRouter(prefix="/customer", tags=["Customer"])


@router.get("/profile", response_model=ApiResponse[ProfileData])
async def get_profile(user: CurrentUser) -> ApiResponse[ProfileData]:
    return ApiResponse(message="Profile retrieved", data=ProfileData.model_validate(user))


@router.patch("/profile", response_model=ApiResponse[ProfileData])
async def update_profile(
    payload: ProfileUpdate, session: SessionDep, user: CurrentUser
) -> ApiResponse[ProfileData]:
    return ApiResponse(
        message="Profile updated",
        data=await CustomerService(session).update_profile(user, payload),
    )


@router.get("/addresses", response_model=ApiResponse[list[AddressData]])
async def list_addresses(session: SessionDep, user: CurrentUser) -> ApiResponse[list[AddressData]]:
    return ApiResponse(
        message="Addresses retrieved",
        data=await CustomerService(session).list_addresses(user.id),
    )


@router.post(
    "/addresses", response_model=ApiResponse[AddressData], status_code=status.HTTP_201_CREATED
)
async def add_address(
    payload: AddressInput, session: SessionDep, user: CurrentUser
) -> ApiResponse[AddressData]:
    return ApiResponse(
        message="Address added", data=await CustomerService(session).add_address(user.id, payload)
    )


@router.put("/addresses/{address_id}", response_model=ApiResponse[AddressData])
async def update_address(
    address_id: int,
    payload: AddressInput,
    session: SessionDep,
    user: CurrentUser,
) -> ApiResponse[AddressData]:
    data = await CustomerService(session).update_address(user.id, address_id, payload)
    return ApiResponse(message="Address updated", data=data)


@router.patch("/addresses/{address_id}/default", response_model=ApiResponse[AddressData])
async def set_default_address(
    address_id: int, session: SessionDep, user: CurrentUser
) -> ApiResponse[AddressData]:
    data = await CustomerService(session).set_default(user.id, address_id)
    return ApiResponse(message="Default address updated", data=data)


@router.delete("/addresses/{address_id}", response_model=ApiResponse[None])
async def delete_address(
    address_id: int, session: SessionDep, user: CurrentUser
) -> ApiResponse[None]:
    await CustomerService(session).delete_address(user.id, address_id)
    return ApiResponse(message="Address deleted", data=None)
