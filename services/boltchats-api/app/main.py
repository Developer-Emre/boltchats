from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI

from app.core.config import settings
from app.core.database import close_db, connect_db
from app.core.redis import close_redis, connect_redis, get_redis
from app.exceptions.handlers import register_exception_handlers
from app.middlewares.cors import register_cors
from app.middlewares.logging import LoggingMiddleware, configure_structlog
from app.middlewares.rate_limit import RateLimitMiddleware
from app.routers import auth
from app.utils.constants import SERVICE_NAME

configure_structlog()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await connect_db()
    await connect_redis()
    app.state.redis = get_redis()
    await logger.ainfo("startup_complete", service=SERVICE_NAME)
    yield
    await close_db()
    await close_redis()
    await logger.ainfo("shutdown_complete", service=SERVICE_NAME)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

register_cors(app)
register_exception_handlers(app)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(LoggingMiddleware)

# Auth router (legacy, will be updated in Step 2)
app.include_router(auth.router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": SERVICE_NAME}
