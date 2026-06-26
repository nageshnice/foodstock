import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.schemas.response import ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)


class AppException(Exception):
    """Base exception for expected application errors."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        code: str = "application_error",
        details: Any | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details
        super().__init__(message)


def _error_response(
    *,
    status_code: int,
    message: str,
    code: str,
    details: Any | None = None,
) -> JSONResponse:
    body = ErrorResponse(
        message=message,
        error=ErrorDetail(code=code, details=details),
    )
    return JSONResponse(status_code=status_code, content=body.model_dump(mode="json"))


async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
    return _error_response(
        status_code=exc.status_code,
        message=exc.message,
        code=exc.code,
        details=exc.details,
    )


async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else "Request failed"
    details = None if isinstance(exc.detail, str) else exc.detail
    return _error_response(
        status_code=exc.status_code,
        message=message,
        code="http_error",
        details=details,
    )


async def validation_exception_handler(
    _: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return _error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        message="Request validation failed",
        code="validation_error",
        details=[
            {key: value for key, value in error.items() if key != "ctx"} for error in exc.errors()
        ],
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error while processing %s %s", request.method, request.url.path)
    return _error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="Internal server error",
        code="internal_server_error",
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register the shared API exception-to-response mappings."""

    app.add_exception_handler(AppException, app_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)
