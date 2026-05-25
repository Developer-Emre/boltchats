import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions.http_exceptions import DatabaseException

logger = structlog.get_logger()


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DatabaseException)
    async def database_exception_handler(
        request: Request, exc: DatabaseException
    ) -> JSONResponse:
        await logger.awarning(
            "database_error", detail=exc.detail, path=request.url.path
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal database error occurred"},
        )
