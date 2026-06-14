"""Custom exceptions and FastAPI exception handlers for NeedNow AI."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------


class NeedNowException(Exception):
    """Base exception for all NeedNow AI errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ValidationException(NeedNowException):
    """Raised when input validation fails."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class MemoryException(NeedNowException):
    """Raised when memory engine operations fail."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class AgentException(NeedNowException):
    """Raised when an agent encounters an error."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ProductException(NeedNowException):
    """Raised when product operations fail."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


# ---------------------------------------------------------------------------
# FastAPI Exception Handlers
# ---------------------------------------------------------------------------


async def neednow_exception_handler(
    request: Request,
    exc: NeedNowException,
) -> JSONResponse:
    """Handle all NeedNowException subclasses with 500 status."""
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": exc.message},
    )


async def validation_exception_handler(
    request: Request,
    exc: ValidationException,
) -> JSONResponse:
    """Handle ValidationException with 400 status."""
    return JSONResponse(
        status_code=400,
        content={"success": False, "error": exc.message},
    )
