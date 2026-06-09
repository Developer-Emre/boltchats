import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI

from app.consumer import consume
from app.core.config import settings
from app.core.database import close_db, connect_db, get_database
from app.core.redis import close_redis, connect_redis, get_redis
from app.storage import MessageRepository
from app.utils.constants import SERVICE_NAME
from app.utils.metrics import get_stats

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await connect_db()
    await connect_redis()
    logger.info("storage.startup", service=SERVICE_NAME)

    repo = MessageRepository(get_database(), get_redis())
    consumer_task = asyncio.create_task(consume(get_redis(), repo))

    yield

    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass

    await close_redis()
    await close_db()
    logger.info("storage.shutdown", service=SERVICE_NAME)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)


@app.get("/health")
async def health_check() -> dict[str, str | dict]:
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "version": settings.app_version,
        "stats": get_stats(),
    }
