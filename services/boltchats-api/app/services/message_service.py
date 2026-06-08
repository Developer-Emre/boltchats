import structlog
from pymongo.errors import PyMongoError

from app.exceptions.http_exceptions import DatabaseException, NotFoundException
from app.schemas.message_schema import MessageListResponse, MessageResponse
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
