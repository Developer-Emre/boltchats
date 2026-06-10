from enum import IntEnum, StrEnum

SERVICE_NAME: str = "boltchats-ws"


class WsCloseCode(IntEnum):
    NORMAL = 1000
    INTERNAL_ERROR = 1011
    UNAUTHORIZED = 4001
    FORBIDDEN = 4003
    RATE_LIMITED = 4029


class EventType(StrEnum):
    # Incoming
    MESSAGE = "message"
    JOIN_ROOM = "join_room"
    LEAVE_ROOM = "leave_room"
    MESSAGE_EDITED = "message_edited"
    MESSAGE_DELETED = "message_deleted"
    REACTION_ADDED = "reaction_added"
    REACTION_REMOVED = "reaction_removed"
    PING = "ping"
    # Outgoing
    PONG = "pong"
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    # Sent only to the message sender — never broadcast to the room
    MESSAGE_CONFIRMED = "message_confirmed"
    ERROR = "error"


# Presence — keys shared with boltchats-api (read-only there)
REDIS_PREFIX_PRESENCE_ROOM: str = "presence:room:"
REDIS_KEY_PRESENCE_ONLINE: str = "presence:online"

# Write-Behind Queue — consumed by boltchats-storage via BRPOP
REDIS_QUEUE_MESSAGES: str = "messages:queue"

# Pub/Sub channel prefix — pattern subscribed as "room:*"
REDIS_CHANNEL_ROOM_PREFIX: str = "room:"

# Rate-limit key prefix for WebSocket messages
REDIS_PREFIX_RATE_LIMIT_WS: str = "ratelimit:ws:"
