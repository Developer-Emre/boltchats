"""
Error handlers and exception converters

Converts domain exceptions to HTTP responses
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
import structlog

from app.exceptions import (
    AppError,
    NotFoundError,
    ConflictError,
    ValidationError,
    UnauthorizedError,
    ForbiddenError,
)

logger = structlog.get_logger()


def register_error_handlers(app: FastAPI) -> None:
    """Register error handlers with FastAPI app"""

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError):
        logger.warning(
            "not_found_error",
            path=request.url.path,
            detail=str(exc),
        )
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc), "error_code": "NOT_FOUND"},
        )

    @app.exception_handler(ConflictError)
    async def conflict_handler(request: Request, exc: ConflictError):
        logger.warning(
            "conflict_error",
            path=request.url.path,
            detail=str(exc),
        )
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc), "error_code": "CONFLICT"},
        )

    @app.exception_handler(ValidationError)
    async def validation_handler(request: Request, exc: ValidationError):
        logger.warning(
            "validation_error",
            path=request.url.path,
            detail=str(exc),
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc), "error_code": "VALIDATION_ERROR"},
        )

    @app.exception_handler(UnauthorizedError)
    async def unauthorized_handler(request: Request, exc: UnauthorizedError):
        logger.warning(
            "unauthorized_error",
            path=request.url.path,
        )
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": str(exc), "error_code": "UNAUTHORIZED"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(ForbiddenError)
    async def forbidden_handler(request: Request, exc: ForbiddenError):
        logger.warning(
            "forbidden_error",
            path=request.url.path,
            detail=str(exc),
        )
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": str(exc), "error_code": "FORBIDDEN"},
        )

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        logger.error(
            "app_error",
            path=request.url.path,
            detail=str(exc),
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": str(exc), "error_code": "INTERNAL_ERROR"},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(
            "unhandled_error",
            path=request.url.path,
            error_type=type(exc).__name__,
            detail=str(exc),
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error", "error_code": "INTERNAL_ERROR"},
        )
