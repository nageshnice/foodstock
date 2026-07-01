from fastapi import APIRouter

from app.core.dependencies import SessionDep
from app.schemas.response import ApiResponse
from app.schemas.settings import ContentPageData
from app.services.settings import SettingsService

router = APIRouter(prefix="/content", tags=["Content"])


@router.get(
    "/terms-and-conditions",
    response_model=ApiResponse[ContentPageData],
    summary="Terms and conditions",
)
async def terms_and_conditions(session: SessionDep) -> ApiResponse[ContentPageData]:
    return ApiResponse(
        message="Terms and conditions retrieved",
        data=await SettingsService(session).get_public_content("terms-and-conditions"),
    )


@router.get(
    "/privacy-policy",
    response_model=ApiResponse[ContentPageData],
    summary="Privacy policy",
)
async def privacy_policy(session: SessionDep) -> ApiResponse[ContentPageData]:
    return ApiResponse(
        message="Privacy policy retrieved",
        data=await SettingsService(session).get_public_content("privacy-policy"),
    )


@router.get(
    "/contact-us",
    response_model=ApiResponse[ContentPageData],
    summary="Contact us",
)
async def contact_us(session: SessionDep) -> ApiResponse[ContentPageData]:
    return ApiResponse(
        message="Contact page retrieved",
        data=await SettingsService(session).get_public_content("contact-us"),
    )
