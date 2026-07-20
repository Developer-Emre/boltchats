from datetime import datetime, timezone
from bson.objectid import ObjectId

import structlog
from pymongo import ReturnDocument
from pymongo.errors import PyMongoError

from app.exceptions.http_exceptions import (
    DatabaseException,
    ForbiddenException,
    NotFoundException,
)
from app.schemas.channel_schema import (
    CreateChannelRequest,
    UpdateChannelRequest,
    ChannelResponse,
    ChannelDetailResponse,
    ChannelListResponse,
    ChannelSettingsSchema,
)
from app.utils.constants import Collection, ErrorMessage
from app.utils.helpers import parse_object_id, generate_slug

logger = structlog.get_logger()

_DEFAULT_LIMIT: int = 20
_MAX_LIMIT: int = 100


def _doc_to_channel(doc: dict) -> ChannelResponse:
    return ChannelResponse(
        id=str(doc["_id"]),
        workspace_id=doc["workspace_id"],
        name=doc["name"],
        display_name=doc.get("display_name", doc["name"]),
        description=doc.get("description", ""),
        type=doc.get("type", "public"),
        topic=doc.get("topic", ""),
        owner_id=doc["owner_id"],
        member_count=doc.get("member_count", 0),
        message_count=doc.get("message_count", 0),
        is_archived=doc.get("is_archived", False),
        is_default=doc.get("is_default", False),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


def _doc_to_channel_detail(doc: dict) -> ChannelDetailResponse:
    return ChannelDetailResponse(
        id=str(doc["_id"]),
        workspace_id=doc["workspace_id"],
        name=doc["name"],
        display_name=doc.get("display_name", doc["name"]),
        description=doc.get("description", ""),
        type=doc.get("type", "public"),
        topic=doc.get("topic", ""),
        purpose=doc.get("purpose", ""),
        owner_id=doc["owner_id"],
        members=doc.get("members", []),
        settings=ChannelSettingsSchema(**doc.get("settings", {})),
        member_count=doc.get("member_count", 0),
        message_count=doc.get("message_count", 0),
        is_archived=doc.get("is_archived", False),
        is_default=doc.get("is_default", False),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


async def create(
    workspace_id: str,
    payload: CreateChannelRequest,
    owner_id: str,
    db,
) -> ChannelResponse:
    """Create a new channel in workspace."""
    now = datetime.now(timezone.utc)
    name_slug = generate_slug(payload.name)

    doc = {
        "workspace_id": workspace_id,
        "name": name_slug,
        "display_name": payload.name,
        "description": payload.description,
        "type": payload.type,
        "topic": payload.topic,
        "purpose": payload.purpose,
        "owner_id": owner_id,
        "members": [owner_id],
        "settings": {},
        "is_archived": False,
        "is_default": False,
        "message_count": 0,
        "member_count": 1,
        "last_message_at": None,
        "shared_workspaces": [],
        "created_at": now,
        "updated_at": now,
    }

    try:
        result = await db[Collection.CHANNELS].insert_one(doc)
    except PyMongoError as exc:
        raise DatabaseException("Failed to create channel") from exc

    doc["_id"] = result.inserted_id
    await logger.ainfo(
        "channel_created",
        channel_id=str(result.inserted_id),
        workspace_id=workspace_id,
        owner_id=owner_id,
        channel_name=payload.name,
    )

    # Update workspace channel count
    try:
        await db[Collection.WORKSPACES].update_one(
            {"_id": ObjectId(workspace_id)},
            {"$inc": {"channel_count": 1}},
        )
    except PyMongoError as exc:
        await logger.aerror("Failed to update workspace channel count", exc_info=True)

    return _doc_to_channel(doc)


async def get_by_id(
    workspace_id: str, channel_id: str, db
) -> ChannelResponse:
    """Get channel by ID."""
    oid = parse_object_id(channel_id, ErrorMessage.CHANNEL_NOT_FOUND)
    try:
        doc = await db[Collection.CHANNELS].find_one(
            {"_id": oid, "workspace_id": workspace_id}
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to query channel") from exc

    if not doc:
        raise NotFoundException(ErrorMessage.CHANNEL_NOT_FOUND)

    return _doc_to_channel(doc)


async def get_detail(
    workspace_id: str, channel_id: str, db
) -> ChannelDetailResponse:
    """Get channel with full details."""
    oid = parse_object_id(channel_id, ErrorMessage.CHANNEL_NOT_FOUND)
    try:
        doc = await db[Collection.CHANNELS].find_one(
            {"_id": oid, "workspace_id": workspace_id}
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to query channel") from exc

    if not doc:
        raise NotFoundException(ErrorMessage.CHANNEL_NOT_FOUND)

    return _doc_to_channel_detail(doc)


async def list_by_workspace(
    workspace_id: str,
    db,
    cursor: str | None = None,
    limit: int = _DEFAULT_LIMIT,
) -> ChannelListResponse:
    """List all channels in workspace."""
    limit = min(limit, _MAX_LIMIT)
    query: dict = {"workspace_id": workspace_id, "is_archived": False}

    if cursor:
        cursor_oid = parse_object_id(cursor, ErrorMessage.INVALID_ID)
        query["_id"] = {"$gt": cursor_oid}

    try:
        docs = (
            await db[Collection.CHANNELS]
            .find(query)
            .sort("_id", 1)
            .limit(limit + 1)
            .to_list(limit + 1)
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to list channels") from exc

    has_more = len(docs) > limit
    items = [_doc_to_channel(d) for d in docs[:limit]]
    next_cursor = str(docs[limit - 1]["_id"]) if has_more else None

    return ChannelListResponse(items=items, next_cursor=next_cursor)


async def update(
    workspace_id: str,
    channel_id: str,
    payload: UpdateChannelRequest,
    user_id: str,
    db,
) -> ChannelResponse:
    """Update channel (owner only)."""
    oid = parse_object_id(channel_id, ErrorMessage.CHANNEL_NOT_FOUND)

    # Get existing channel
    try:
        existing = await db[Collection.CHANNELS].find_one(
            {"_id": oid, "workspace_id": workspace_id}
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to query channel") from exc

    if not existing:
        raise NotFoundException(ErrorMessage.CHANNEL_NOT_FOUND)

    # Check ownership
    if existing["owner_id"] != user_id:
        raise ForbiddenException(ErrorMessage.WORKSPACE_OWNER_ONLY)

    # Build update doc
    update_data = {}
    if payload.name:
        update_data["display_name"] = payload.name
        update_data["name"] = generate_slug(payload.name)
    if payload.description is not None:
        update_data["description"] = payload.description
    if payload.topic is not None:
        update_data["topic"] = payload.topic
    if payload.purpose is not None:
        update_data["purpose"] = payload.purpose
    if payload.settings:
        update_data["settings"] = payload.settings.dict()

    update_data["updated_at"] = datetime.now(timezone.utc)

    try:
        doc = await db[Collection.CHANNELS].find_one_and_update(
            {"_id": oid},
            {"$set": update_data},
            return_document=ReturnDocument.AFTER,
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to update channel") from exc

    await logger.ainfo(
        "channel_updated",
        channel_id=channel_id,
        workspace_id=workspace_id,
        updated_by=user_id,
    )

    return _doc_to_channel(doc)


async def add_member(
    workspace_id: str, channel_id: str, member_id: str, added_by: str, db
) -> ChannelResponse:
    """Add a member to channel."""
    oid = parse_object_id(channel_id, ErrorMessage.CHANNEL_NOT_FOUND)

    try:
        doc = await db[Collection.CHANNELS].find_one_and_update(
            {"_id": oid, "workspace_id": workspace_id, "members": {"$ne": member_id}},
            {
                "$push": {"members": member_id},
                "$inc": {"member_count": 1},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
            return_document=ReturnDocument.AFTER,
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to add member to channel") from exc

    if not doc:
        raise NotFoundException(ErrorMessage.CHANNEL_NOT_FOUND)

    await logger.ainfo(
        "channel_member_added",
        channel_id=channel_id,
        workspace_id=workspace_id,
        member_id=member_id,
        added_by=added_by,
    )

    return _doc_to_channel(doc)


async def remove_member(
    workspace_id: str, channel_id: str, member_id: str, removed_by: str, db
) -> ChannelResponse:
    """Remove a member from channel."""
    oid = parse_object_id(channel_id, ErrorMessage.CHANNEL_NOT_FOUND)

    # Get channel to check if member is owner
    try:
        channel = await db[Collection.CHANNELS].find_one(
            {"_id": oid, "workspace_id": workspace_id}
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to query channel") from exc

    if not channel:
        raise NotFoundException(ErrorMessage.CHANNEL_NOT_FOUND)

    # Prevent removing owner
    if channel["owner_id"] == member_id:
        raise ForbiddenException("Cannot remove channel owner")

    try:
        doc = await db[Collection.CHANNELS].find_one_and_update(
            {"_id": oid},
            {
                "$pull": {"members": member_id},
                "$inc": {"member_count": -1},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
            return_document=ReturnDocument.AFTER,
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to remove member from channel") from exc

    await logger.ainfo(
        "channel_member_removed",
        channel_id=channel_id,
        workspace_id=workspace_id,
        member_id=member_id,
        removed_by=removed_by,
    )

    return _doc_to_channel(doc)


async def archive(
    workspace_id: str, channel_id: str, user_id: str, db
) -> ChannelResponse:
    """Archive a channel (owner only)."""
    oid = parse_object_id(channel_id, ErrorMessage.CHANNEL_NOT_FOUND)

    # Get existing channel
    try:
        existing = await db[Collection.CHANNELS].find_one(
            {"_id": oid, "workspace_id": workspace_id}
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to query channel") from exc

    if not existing:
        raise NotFoundException(ErrorMessage.CHANNEL_NOT_FOUND)

    # Check ownership
    if existing["owner_id"] != user_id:
        raise ForbiddenException(ErrorMessage.WORKSPACE_OWNER_ONLY)

    try:
        doc = await db[Collection.CHANNELS].find_one_and_update(
            {"_id": oid},
            {
                "$set": {
                    "is_archived": True,
                    "archived_at": datetime.now(timezone.utc),
                    "archived_by": user_id,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
            return_document=ReturnDocument.AFTER,
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to archive channel") from exc

    await logger.ainfo(
        "channel_archived",
        channel_id=channel_id,
        workspace_id=workspace_id,
        archived_by=user_id,
    )

    return _doc_to_channel(doc)


async def verify_member_access(
    workspace_id: str, channel_id: str, user_id: str, db
) -> ChannelResponse:
    """Verify user is member of channel."""
    oid = parse_object_id(channel_id, ErrorMessage.CHANNEL_NOT_FOUND)

    try:
        doc = await db[Collection.CHANNELS].find_one(
            {"_id": oid, "workspace_id": workspace_id, "members": user_id}
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to query channel") from exc

    if not doc:
        raise ForbiddenException(ErrorMessage.WORKSPACE_ACCESS_DENIED)

    return _doc_to_channel(doc)
