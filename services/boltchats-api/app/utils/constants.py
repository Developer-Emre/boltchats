from enum import StrEnum

# Redis key prefixes
REDIS_PREFIX_REFRESH_TOKEN: str = "refresh_token:"
REDIS_PREFIX_RATE_LIMIT: str = "rate_limit:"
REDIS_PREFIX_PRESENCE_ROOM: str = "presence:room:"
REDIS_KEY_PRESENCE_ONLINE: str = "presence:online"

# Service name
SERVICE_NAME: str = "boltchats-api"


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


class Collection(StrEnum):
    USERS = "users"
    ROOMS = "rooms"
    MESSAGES = "messages"


class ErrorMessage(StrEnum):
    USER_NOT_FOUND = "User not found"
    USER_ALREADY_EXISTS = "User already exists"
    INVALID_CREDENTIALS = "Invalid credentials"
    INVALID_TOKEN = "Invalid or expired token"
    REFRESH_TOKEN_NOT_FOUND = "Refresh token not found or expired"
    RATE_LIMIT_EXCEEDED = "Rate limit exceeded"
    UNAUTHORIZED = "Not authenticated"
    ROOM_NOT_FOUND = "Room not found"
    OWNER_CANNOT_LEAVE = "Room owner cannot leave the room"
    INVALID_ID = "Invalid resource ID"
