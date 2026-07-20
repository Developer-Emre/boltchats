from datetime import datetime, timezone

import structlog
from pymongo import ReturnDocument
from pymongo.errors import PyMongoError

from app.exceptions.http_exceptions import (
    DatabaseException,
    ForbiddenException,
    NotFoundException,
)
from app.schemas.message_schema import (
    EditMessageRequest,
    MessageListResponse,
    MessageResponse,
)
from app.utils.constants import Collection, ErrorMessage
from app.utils.helpers import parse_object_id

logger = structlog.get_logger()

_DEFAULT_LIMIT: int = 50
_MAX_LIMIT: int = 100


def _doc_to_message(doc: dict) -> MessageResponse:
    return MessageResponse(
        id=str(doc["_id"]),
        room_id=doc.get("channel_id", doc.get("room_id", "")),
        sender_id=doc["sender_id"],
        content=doc["content"],
        created_at=doc["created_at"],
        edited_at=doc.get("edited_at"),
        deleted_at=doc.get("deleted_at"),
        is_deleted=doc.get("deleted_at") is not None,
    )


async def get_history(
    workspace_id: str,
    channel_id: str,
    user_id: str,
    db,
    before: str | None = None,
    limit: int = _DEFAULT_LIMIT,
) -> MessageListResponse:
    """Get message history for a channel."""
    limit = min(limit, _MAX_LIMIT)

    channel_oid = parse_object_id(channel_id, ErrorMessage.CHANNEL_NOT_FOUND)

    # Verify user is member of channel (already checked by middleware, but double-check)
    try:
        channel = await db[Collection.CHANNELS].find_one(
            {"_id": channel_oid, "workspace_id": workspace_id}
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to query channel") from exc

    if not channel:
        raise NotFoundException(ErrorMessage.CHANNEL_NOT_FOUND)

    if user_id not in channel.get("members", []):
        raise ForbiddenException(ErrorMessage.WORKSPACE_ACCESS_DENIED)

    # Query messages
    query: dict = {"workspace_id": workspace_id, "channel_id": channel_id}
    if before:
        before_oid = parse_object_id(before, ErrorMessage.INVALID_ID)
        query["_id"] = {"$lt": before_oid}

    try:
        docs = (
            await db[Collection.MESSAGES]
            .find(query)
            .sort("_id", -1)
            .limit(limit + 1)
            .to_list(limit + 1)
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to fetch message history") from exc

    has_more = len(docs) > limit
    items = [_doc_to_message(d) for d in reversed(docs[:limit])]
    next_before = str(docs[limit - 1]["_id"]) if has_more else None

    return MessageListResponse(items=items, next_cursor=next_before)


async def create(
    workspace_id: str, channel_id: str, content: str, sender_id: str, db
) -> MessageResponse:
    """Create a message in channel."""
    now = datetime.now(timezone.utc)

    doc = {
        "workspace_id": workspace_id,
        "channel_id": channel_id,
        "sender_id": sender_id,
        "content": content,
        "created_at": now,
        "edited_at": None,
        "deleted_at": None,
    }

    try:
        result = await db[Collection.MESSAGES].insert_one(doc)
    except PyMongoError as exc:
        raise DatabaseException("Failed to create message") from exc

    doc["_id"] = result.inserted_id

    # Update channel message count and last_message_at
    try:
        await db[Collection.CHANNELS].update_one(
            {"_id": parse_object_id(channel_id, ErrorMessage.CHANNEL_NOT_FOUND)},
            {
                "$inc": {"message_count": 1},
                "$set": {"last_message_at": now, "updated_at": now},
            },
        )
    except PyMongoError as exc:
        await logger.aerror("Failed to update channel stats", exc_info=True)

    # Update workspace message count
    try:
        await db[Collection.WORKSPACES].update_one(
            {"_id": parse_object_id(workspace_id, ErrorMessage.WORKSPACE_NOT_FOUND)},
            {"$inc": {"message_count": 1}},
        )
    except PyMongoError as exc:
        await logger.aerror("Failed to update workspace stats", exc_info=True)

    await logger.ainfo(
        "message_created",
        message_id=str(result.inserted_id),
        workspace_id=workspace_id,
        channel_id=channel_id,
        sender_id=sender_id,
    )

    return _doc_to_message(doc)


async def edit(
    workspace_id: str,
    channel_id: str,
    message_id: str,
    payload: EditMessageRequest,
    user_id: str,
    db,
) -> MessageResponse:
    """Edit a message (sender only)."""
    oid = parse_object_id(message_id, ErrorMessage.INVALID_ID)

    # Get existing message
    try:
        existing = await db[Collection.MESSAGES].find_one(
            {"_id": oid, "workspace_id": workspace_id, "channel_id": channel_id}
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to query message") from exc

    if not existing:
        raise NotFoundException(ErrorMessage.INVALID_ID)

    # Verify user is sender
    if existing["sender_id"] != user_id:
        raise ForbiddenException("Only message sender can edit")

    now = datetime.now(timezone.utc)

    try:
        doc = await db[Collection.MESSAGES].find_one_and_update(
            {"_id": oid},
            {
                "$set": {
                    "content": payload.content,
                    "edited_at": now,
                }
            },
            return_document=ReturnDocument.AFTER,
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to edit message") from exc

    await logger.ainfo(
        "message_edited",
        message_id=message_id,
        workspace_id=workspace_id,
        channel_id=channel_id,
        edited_by=user_id,
    )

    return _doc_to_message(doc)


async def delete(
    workspace_id: str,
    channel_id: str,
    message_id: str,
    user_id: str,
    db,
) -> MessageResponse:
    """Delete a message (sender or admin only)."""
    oid = parse_object_id(message_id, ErrorMessage.INVALID_ID)

    # Get existing message
    try:
        existing = await db[Collection.MESSAGES].find_one(
            {"_id": oid, "workspace_id": workspace_id, "channel_id": channel_id}
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to query message") from exc

    if not existing:
        raise NotFoundException(ErrorMessage.INVALID_ID)

    # Verify user is sender or admin
    if existing["sender_id"] != user_id:
        # TODO: Check if user is admin
        raise ForbiddenException("Only message sender or admin can delete")

    now = datetime.now(timezone.utc)

    try:
        doc = await db[Collection.MESSAGES].find_one_and_update(
            {"_id": oid},
            {
                "$set": {
                    "deleted_at": now,
                }
            },
            return_document=ReturnDocument.AFTER,
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to delete message") from exc

    # Update channel message count (decrement)
    try:
        await db[Collection.CHANNELS].update_one(
            {"_id": parse_object_id(channel_id, ErrorMessage.CHANNEL_NOT_FOUND)},
            {"$inc": {"message_count": -1}},
        )
    except PyMongoError as exc:
        await logger.aerror("Failed to update channel stats", exc_info=True)

    # Update workspace message count
    try:
        await db[Collection.WORKSPACES].update_one(
            {"_id": parse_object_id(workspace_id, ErrorMessage.WORKSPACE_NOT_FOUND)},
            {"$inc": {"message_count": -1}},
        )
    except PyMongoError as exc:
        await logger.aerror("Failed to update workspace stats", exc_info=True)

    await logger.ainfo(
        "message_deleted",
        message_id=message_id,
        workspace_id=workspace_id,
        channel_id=channel_id,
        deleted_by=user_id,
    )

    return _doc_to_message(doc)


async def get_dm_history(
    workspace_id: str,
    dm_id: str,
    user_id: str,
    db,
    before: str | None = None,
    limit: int = _DEFAULT_LIMIT,
) -> MessageListResponse:
    """Get message history for a DM group."""
    limit = min(limit, _MAX_LIMIT)

    dm_oid = parse_object_id(dm_id, ErrorMessage.INVALID_ID)

    # Verify user is participant of DM (already checked by middleware, but double-check)
    try:
        dm = await db[Collection.DIRECT_MESSAGES].find_one(
            {"_id": dm_oid, "workspace_id": workspace_id}
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to query DM") from exc

    if not dm:
        raise NotFoundException(ErrorMessage.INVALID_ID)

    if user_id not in dm.get("participants", []):
        raise ForbiddenException(ErrorMessage.WORKSPACE_ACCESS_DENIED)

    # Query messages
    query: dict = {"workspace_id": workspace_id, "dm_id": dm_id}
    if before:
        before_oid = parse_object_id(before, ErrorMessage.INVALID_ID)
        query["_id"] = {"$lt": before_oid}

    try:
        docs = (
            await db[Collection.MESSAGES]
            .find(query)
            .sort("_id", -1)
            .limit(limit + 1)
            .to_list(limit + 1)
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to fetch DM history") from exc

    has_more = len(docs) > limit
    items = [_doc_to_message(d) for d in reversed(docs[:limit])]
    next_before = str(docs[limit - 1]["_id"]) if has_more else None

    return MessageListResponse(items=items, next_cursor=next_before)


async def create_dm(
    workspace_id: str, dm_id: str, content: str, sender_id: str, db
) -> MessageResponse:
    """Create a message in DM group."""
    now = datetime.now(timezone.utc)

    doc = {
        "workspace_id": workspace_id,
        "dm_id": dm_id,
        "sender_id": sender_id,
        "content": content,
        "created_at": now,
        "edited_at": None,
        "deleted_at": None,
    }

    try:
        result = await db[Collection.MESSAGES].insert_one(doc)
    except PyMongoError as exc:
        raise DatabaseException("Failed to create DM message") from exc

    doc["_id"] = result.inserted_id

    # Update DM message count
    try:
        await db[Collection.DIRECT_MESSAGES].update_one(
            {"_id": parse_object_id(dm_id, ErrorMessage.INVALID_ID)},
            {
                "$inc": {"message_count": 1},
                "$set": {"updated_at": now},
            },
        )
    except PyMongoError as exc:
        await logger.aerror("Failed to update DM stats", exc_info=True)

    await logger.ainfo(
        "dm_message_created",
        message_id=str(result.inserted_id),
        workspace_id=workspace_id,
        dm_id=dm_id,
        sender_id=sender_id,
    )

    return _doc_to_message(doc)
