from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Depends
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

from app.core.config import settings
from app.core.database import close_db, connect_db, get_database
from app.core.redis import close_redis, connect_redis, get_redis
from app.error_handlers import register_error_handlers
from app.middlewares.cors import register_cors
from app.middlewares.logging import LoggingMiddleware, configure_structlog
from app.middlewares.rate_limit import RateLimitMiddleware
from app.middlewares.prometheus import PrometheusMiddleware
from app.routers import (
    auth_router,
    conversations_router,
    organizations_router,
    integrations_router,
)
from app.utils.constants import SERVICE_NAME
from app.database import DatabaseHealth
from app.repositories import OrganizationRepository, UserRepository

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

# Register middleware (CORS, logging, rate limiting, Prometheus)
app.add_middleware(PrometheusMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(LoggingMiddleware)
register_cors(app)

# Register error handlers (converts AppError to HTTP responses)
register_error_handlers(app)

# Mount routers under /api/v1
app.include_router(auth_router, prefix="/api/v1")
app.include_router(conversations_router, prefix="/api/v1")
# TODO: Fix organizations router Depends()
# app.include_router(organizations_router, prefix="/api/v1")
app.include_router(integrations_router, prefix="/api/v1")


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await connect_db()
    await connect_redis()
    app.state.redis = get_redis()

    # Ensure critical unique indexes exist (idempotent — safe to run every startup)
    db = get_database()
    org_repo = OrganizationRepository(db)
    await org_repo.create_index("slug", unique=True)

    user_repo = UserRepository(db)
    await user_repo.create_index("email", unique=True)  # aynı race condition email için de geçerli

    logger.info("startup_complete", service=SERVICE_NAME)
    yield
    await close_db()
    await close_redis()
    logger.info("shutdown_complete", service=SERVICE_NAME)
