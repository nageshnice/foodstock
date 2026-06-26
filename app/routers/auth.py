from fastapi import APIRouter, Request, status

from app.core.dependencies import SessionDep
from app.core.rate_limit import enforce_rate_limit
from app.schemas.auth import LoginRequest, SignupRequest, TokenData
from app.schemas.response import ApiResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=ApiResponse[TokenData], status_code=status.HTTP_201_CREATED)
async def signup(
    payload: SignupRequest, session: SessionDep, request: Request
) -> ApiResponse[TokenData]:
    enforce_rate_limit(request, max_requests=10)
    return ApiResponse(message="Account created", data=await AuthService(session).signup(payload))


@router.post("/login", response_model=ApiResponse[TokenData])
async def login(
    payload: LoginRequest, session: SessionDep, request: Request
) -> ApiResponse[TokenData]:
    enforce_rate_limit(request, max_requests=15)
    return ApiResponse(message="Login successful", data=await AuthService(session).login(payload))
