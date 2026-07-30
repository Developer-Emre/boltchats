from enum import StrEnum

# Service name
SERVICE_NAME: str = "boltchats-api"


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


# Re-export SparkQuark constants for convenience
from app.utils.sparkquark_constants import Collection, ErrorMessage, RedisKey

__all__ = ["SERVICE_NAME", "TokenType", "Collection", "ErrorMessage", "RedisKey"]
