from enum import StrEnum

# Service name
SERVICE_NAME: str = "boltchats-api"


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


# Redis prefixes
REDIS_PREFIX_RATE_LIMIT: str = "ratelimit:"
REDIS_PREFIX_REFRESH_TOKEN: str = "refresh_token:"
REDIS_PREFIX_SESSION: str = "session:"


# Re-export SparkQuark constants for convenience
from app.utils.sparkquark_constants import Collection, ErrorMessage, RedisKey

__all__ = [
    "SERVICE_NAME",
    "TokenType",
    "REDIS_PREFIX_RATE_LIMIT",
    "REDIS_PREFIX_REFRESH_TOKEN",
    "REDIS_PREFIX_SESSION",
    "Collection",
    "ErrorMessage",
    "RedisKey",
]
