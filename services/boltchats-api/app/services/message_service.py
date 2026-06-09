import structlog
from datetime import datetime, timezone

from pymongo.errors import PyMongoError
from redis.asyncio import Redis

from app.exceptions.http_exceptions import DatabaseException, ForbiddenException, NotFoundException
from app.schemas.message_schema import EditMessageRequest, MessageListResponse, MessageResponse
from app.utils.constants import Collection, ErrorMessage
from app.utils.helpers import parse_object_id

logger = structlog.get_logger()

_DEFAULT_LIMIT: int = 50
_MAX_LIMIT: int = 100
_REDIS_PREFIX_MESSAGE_ID_MAP = "message:id:"


def _doc_to_message(doc: dict) -> MessageResponse:
    return MessageResponse(
        id=str(doc["_id"]),
        room_id=doc["room_id"],
        sender_id=doc["sender_id"],
        content=doc["content"],
        created_at=doc["created_at"],
        edited_at=doc.get("edited_at"),
        deleted_at=doc.get("deleted_at"),
        is_deleted=doc.get("deleted_at") is not None,
    )


async def _resolve_message_id(message_id: str, db, redis: Redis | None) -> str:
    """Resolve message_id (UUID or ObjectId) to MongoDB ObjectId.
    
    1. Try parsing as ObjectId → return
    2. Try Redis cache (UUID → ObjectId mapping)
    3. Query MongoDB by UUID field
    4. Raise NotFoundException if not found
    """
    # Try to parse as ObjectId first
    try:
        return parse_object_id(message_id, "")
    except Exception:
        pass
    
    # Try Redis cache
    if redis:
        try:
            cached_oid = await redis.get(f"{_REDIS_PREFIX_MESSAGE_ID_MAP}{message_id}")
            if cached_oid:
                return cached_oid.decode() if isinstance(cached_oid, bytes) else cached_oid
        except Exception as exc:
            logger.warning("message_service.redis_lookup_failed", error=str(exc))
    
    # Query MongoDB by UUID
    try:
        message = await db[Collection.MESSAGES].find_one({"_id": message_id})
        if message:
            return message["_id"]
    except PyMongoError as exc:
        raise DatabaseException("Failed to query message") from exc
    
    raise NotFoundException("Message not found")


async def get_history(
    room_id: str,
    user_id: str,
    db,
    before: str | None = None,
    limit: int = _DEFAULT_LIMIT,
) -> MessageListResponse:
    limit = min(limit, _MAX_LIMIT)

    room_oid = parse_object_id(room_id, ErrorMessage.ROOM_NOT_FOUND)
    try:
        room = await db[Collection.ROOMS].find_one({"_id": room_oid})
    except PyMongoError as exc:
        raise DatabaseException("Failed to query room") from exc

    if not room:
        raise NotFoundException(ErrorMessage.ROOM_NOT_FOUND)

    # Verify user is a member of the room
    if user_id not in room.get("member_ids", []):
        raise NotFoundException(ErrorMessage.ROOM_NOT_FOUND)

    query: dict = {"room_id": room_id}
    if before:
        before_oid = parse_object_id(before, ErrorMessage.INVALID_ID)
        query["_id"] = {"$lt": before_oid}

    try:
        docs = (
            await db[Collection.MESSAGES]
            .find(query)
            .sort("_id", 1)
            .limit(limit + 1)
            .to_list(limit + 1)
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to fetch messages") from exc

    has_more = len(docs) > limit
    items = [_doc_to_message(d) for d in docs[:limit]]
    next_cursor = str(docs[limit - 1]["_id"]) if has_more else None
    return MessageListResponse(items=items, next_cursor=next_cursor)


async def edit_message(
    room_id: str,
    message_id: str,
    user_id: str,
    payload: EditMessageRequest,
    db,
    redis: Redis | None = None,
) -> MessageResponse:
    room_oid = parse_object_id(room_id, ErrorMessage.ROOM_NOT_FOUND)
    
    # Resolve UUID or ObjectId to MongoDB ObjectId
    message_oid = await _resolve_message_id(message_id, db, redis)

    try:
        room = await db[Collection.ROOMS].find_one({"_id": room_oid})
    except PyMongoError as exc:
        raise DatabaseException("Failed to query room") from exc

    if not room:
        raise NotFoundException(ErrorMessage.ROOM_NOT_FOUND)

    if user_id not in room.get("member_ids", []):
        raise NotFoundException(ErrorMessage.ROOM_NOT_FOUND)

    try:
        message = await db[Collection.MESSAGES].find_one({"_id": message_oid})
    except PyMongoError as exc:
        raise DatabaseException("Failed to fetch message") from exc

    if not message:
        raise NotFoundException("Message not found")

    if message["sender_id"] != user_id:
        raise ForbiddenException("Can only edit your own messages")

    if message.get("deleted_at"):
        raise NotFoundException("Cannot edit deleted message")

    try:
        updated = await db[Collection.MESSAGES].find_one_and_update(
            {"_id": message_oid},
            {
                "$set": {
                    "content": payload.content,
                    "edited_at": datetime.now(timezone.utc),
                }
            },
            return_document=True,
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to update message") from exc

    return _doc_to_message(updated)


async def delete_message(
    room_id: str,
    message_id: str,
    user_id: str,
    db,
    redis: Redis | None = None,
) -> None:
    room_oid = parse_object_id(room_id, ErrorMessage.ROOM_NOT_FOUND)
    
    # Resolve UUID or ObjectId to MongoDB ObjectId
    message_oid = await _resolve_message_id(message_id, db, redis)

    try:
        room = await db[Collection.ROOMS].find_one({"_id": room_oid})
    except PyMongoError as exc:
        raise DatabaseException("Failed to query room") from exc

    if not room:
        raise NotFoundException(ErrorMessage.ROOM_NOT_FOUND)

    if user_id not in room.get("member_ids", []):
        raise NotFoundException(ErrorMessage.ROOM_NOT_FOUND)

    try:
        message = await db[Collection.MESSAGES].find_one({"_id": message_oid})
    except PyMongoError as exc:
        raise DatabaseException("Failed to fetch message") from exc

    if not message:
        raise NotFoundException("Message not found")

    if message["sender_id"] != user_id:
        raise ForbiddenException("Can only delete your own messages")

    try:
        await db[Collection.MESSAGES].update_one(
            {"_id": message_oid},
            {"$set": {"deleted_at": datetime.now(timezone.utc)}},
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to delete message") from exc
