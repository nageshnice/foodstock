from fastapi import APIRouter, Depends, Request, status

from app.core.dependencies import CurrentUser, SessionDep, require_permission
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
    return ApiResponse(
        message="Account created",
        data=await AuthService(session).signup(payload, request),
    )


@router.post("/login", response_model=ApiResponse[TokenData])
async def login(
    payload: LoginRequest, session: SessionDep, request: Request
) -> ApiResponse[TokenData]:
    enforce_rate_limit(request, max_requests=15)
    return ApiResponse(
        message="Logged in successfully",
        data=await AuthService(session).login(payload, request),
    )


@router.post("/logout", response_model=ApiResponse[None])
async def logout(
    user: CurrentUser,
    session: SessionDep,
    request: Request,
) -> ApiResponse[None]:
    session_id = None
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        from app.core.security import decode_access_token

        try:
            claims = decode_access_token(auth_header.split(" ", 1)[1])
            session_id = claims.get("session_id")
        except Exception:
            session_id = None
    await AuthService(session).logout(user, session_id)
    return ApiResponse(message="Logged out successfully", data=None)
