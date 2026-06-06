import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.exceptions.http_exceptions import RateLimitException
from app.utils.constants import REDIS_PREFIX_RATE_LIMIT, ErrorMessage

logger = structlog.get_logger()


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting for:
        # - Health checks
        # - WebSocket connections
        # - CORS preflight requests
        if (request.url.path == "/health" or 
            request.url.path.startswith("/ws") or
            request.method == "OPTIONS"):
            return await call_next(request)
        
        redis = request.app.state.redis
        client_ip = request.client.host if request.client else "unknown"
        key = f"{REDIS_PREFIX_RATE_LIMIT}{client_ip}"

        current = await redis.incr(key)
        if current == 1:
            await redis.expire(key, settings.rate_limit_window_seconds)

        if current > settings.rate_limit_requests:
            await logger.awarning(
                "rate_limit_exceeded", ip=client_ip, count=current
            )
            raise RateLimitException(ErrorMessage.RATE_LIMIT_EXCEEDED)

        return await call_next(request)
