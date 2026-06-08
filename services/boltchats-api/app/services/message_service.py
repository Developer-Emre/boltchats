import structlog
from datetime import datetime, timezone

from pymongo.errors import PyMongoError

from app.exceptions.http_exceptions import DatabaseException, ForbiddenException, NotFoundException
from app.schemas.message_schema import EditMessageRequest, MessageListResponse, MessageResponse
from app.utils.constants import Collection, ErrorMessage
from app.utils.helpers import parse_object_id

logger = structlog.get_logger()

_DEFAULT_LIMIT: int = 50
_MAX_LIMIT: int = 100


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
) -> MessageResponse:
    room_oid = parse_object_id(room_id, ErrorMessage.ROOM_NOT_FOUND)
    
    # Try to parse as ObjectId first, if that fails, assume it's a UUID (optimistic client ID)
    # and query by UUID field in the collection
    try:
        message_oid = parse_object_id(message_id, "")
    except Exception:
        # message_id is likely a UUID from client (optimistic placeholder)
        # Query by looking up in collection
        try:
            message = await db[Collection.MESSAGES].find_one({"_id": message_id})
            if message:
                message_oid = message["_id"]
            else:
                raise NotFoundException("Message not found")
        except PyMongoError as exc:
            raise DatabaseException("Failed to query message") from exc

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
) -> None:
    room_oid = parse_object_id(room_id, ErrorMessage.ROOM_NOT_FOUND)
    
    # Try to parse as ObjectId first, if that fails, assume it's a UUID (optimistic client ID)
    try:
        message_oid = parse_object_id(message_id, "")
    except Exception:
        # message_id is likely a UUID from client (optimistic placeholder)
        # Query by looking up in collection
        try:
            message = await db[Collection.MESSAGES].find_one({"_id": message_id})
            if message:
                message_oid = message["_id"]
            else:
                raise NotFoundException("Message not found")
        except PyMongoError as exc:
            raise DatabaseException("Failed to query message") from exc

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
