from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Depends

from app.core.config import settings
from app.core.database import close_db, connect_db, get_database
from app.core.redis import close_redis, connect_redis, get_redis
from app.error_handlers import register_error_handlers
from app.middlewares.cors import register_cors
from app.middlewares.logging import LoggingMiddleware, configure_structlog
from app.middlewares.rate_limit import RateLimitMiddleware
from app.routers import (
    auth_router,
    conversations_router,
    organizations_router,
    integrations_router,
)
from app.utils.sparkquark_constants import SERVICE_NAME
from app.database import DatabaseHealth

configure_structlog()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await connect_db()
    await connect_redis()
    app.state.redis = get_redis()
    logger.info("startup_complete", service=SERVICE_NAME)
    yield
    await close_db()
    await close_redis()
    logger.info("shutdown_complete", service=SERVICE_NAME)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="SparkQuark - Omnichannel Customer Communication Operating System",
    lifespan=lifespan,
)

# Register middleware (CORS, logging, rate limiting)
register_cors(app)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(LoggingMiddleware)

# Register error handlers (converts AppError to HTTP responses)
register_error_handlers(app)

# Mount routers under /api/v1
app.include_router(auth_router, prefix="/api/v1")
app.include_router(conversations_router, prefix="/api/v1")
app.include_router(organizations_router, prefix="/api/v1")
app.include_router(integrations_router, prefix="/api/v1")


@app.get("/health")
async def health_check(db = Depends(get_database)) -> dict:
    """Health check endpoint with database status"""
    try:
        # Quick database connectivity check
        health_checker = DatabaseHealth(db)
        db_check = await health_checker._check_connection()

        return {
            "status": "ok",
            "service": SERVICE_NAME,
            "version": settings.app_version,
            "database": db_check["status"],
        }
    except Exception as e:
        logger.error("health_check_failed", error=str(e))
        return {
            "status": "degraded",
            "service": SERVICE_NAME,
            "version": settings.app_version,
            "database": "error",
            "error": str(e),
        }

