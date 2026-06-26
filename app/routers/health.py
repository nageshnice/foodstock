from typing import Literal

from fastapi import APIRouter, status
from sqlalchemy import text

from app.database.session import engine
from app.schemas.health import HealthData
from app.schemas.response import ApiResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=ApiResponse[HealthData],
    status_code=status.HTTP_200_OK,
    summary="Check application health",
)
async def health_check() -> ApiResponse[HealthData]:
    """Confirm the API process and MySQL database are reachable."""

    db_status: Literal["connected", "disconnected"] = "disconnected"
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    overall: Literal["healthy", "degraded"] = "healthy" if db_status == "connected" else "degraded"
    message = (
        "Food Stock API is healthy"
        if overall == "healthy"
        else "Food Stock API is running but the database is unreachable"
    )
    return ApiResponse(
        message=message,
        data=HealthData(status=overall, database=db_status),
    )
