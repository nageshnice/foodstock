from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class ApiResponse(BaseModel, Generic[DataT]):
    """Standard envelope for successful API responses."""

    success: bool = True
    message: str
    total_count: int | None = None
    data: DataT


class ErrorDetail(BaseModel):
    code: str
    details: Any | None = None


class ErrorResponse(BaseModel):
    """Standard envelope for API errors."""

    success: bool = False
    message: str
    error: ErrorDetail
    data: None = Field(default=None)
