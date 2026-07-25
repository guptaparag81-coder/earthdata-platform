"""Domain exceptions and FastAPI exception handlers."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class EarthDataError(Exception):
    """Base class for all application-specific errors."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "internal_error"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class UpstreamServiceError(EarthDataError):
    """Raised when an upstream data provider (e.g. EONET) fails or is unreachable."""

    status_code = status.HTTP_502_BAD_GATEWAY
    error_code = "upstream_service_error"


class DataValidationError(EarthDataError):
    """Raised when ingested or processed data fails domain validation."""

    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    error_code = "data_validation_error"


class RecordNotFoundError(EarthDataError):
    """Raised when a requested persisted record does not exist."""

    status_code = status.HTTP_404_NOT_FOUND
    error_code = "record_not_found"


def _error_payload(error_code: str, message: str, details: dict[str, Any]) -> dict[str, Any]:
    return {"error": {"code": error_code, "message": message, "details": details}}


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI application."""

    @app.exception_handler(EarthDataError)
    async def handle_earthdata_error(request: Request, exc: EarthDataError) -> JSONResponse:
        logger.warning(
            "handled_application_error",
            extra={"error_code": exc.error_code, "path": request.url.path},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(exc.error_code, exc.message, exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=_error_payload(
                "request_validation_error",
                "Request payload failed validation.",
                {"errors": exc.errors()},
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload("http_error", str(exc.detail), {}),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_exception", extra={"path": request.url.path})
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_payload("internal_error", "An unexpected error occurred.", {}),
        )
