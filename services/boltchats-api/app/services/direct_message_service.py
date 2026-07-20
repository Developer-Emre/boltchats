from datetime import datetime, timezone
from bson.objectid import ObjectId

import structlog
from pymongo import ReturnDocument
from pymongo.errors import PyMongoError

from app.exceptions.http_exceptions import (
    DatabaseException,
    NotFoundException,
    ForbiddenException,
)
from app.schemas.direct_message_schema import (
    CreateDirectMessageRequest,
    DirectMessageResponse,
    DirectMessageDetailResponse,
    DirectMessageListResponse,
)
from app.utils.constants import Collection, ErrorMessage
from app.utils.helpers import parse_object_id

logger = structlog.get_logger()

_DEFAULT_LIMIT: int = 20
_MAX_LIMIT: int = 100


def _doc_to_dm(doc: dict) -> DirectMessageResponse:
    return DirectMessageResponse(
        id=str(doc["_id"]),
        workspace_id=doc["workspace_id"],
        name=doc.get("name", ""),
        participants=doc.get("participants", []),
        participant_count=doc.get("participant_count", 0),
        created_by=doc["created_by"],
        is_archived=doc.get("is_archived", False),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


def _doc_to_dm_detail(doc: dict) -> DirectMessageDetailResponse:
    return DirectMessageDetailResponse(
        id=str(doc["_id"]),
        workspace_id=doc["workspace_id"],
        name=doc.get("name", ""),
        participants=doc.get("participants", []),
        participant_count=doc.get("participant_count", 0),
        created_by=doc["created_by"],
        is_archived=doc.get("is_archived", False),
        message_count=doc.get("message_count", 0),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


async def create(
    workspace_id: str,
    payload: CreateDirectMessageRequest,
    creator_id: str,
    db,
) -> DirectMessageResponse:
    """Create a new direct message group."""
    now = datetime.now(timezone.utc)

    # Ensure creator is in participants
    participants = list(set([creator_id] + payload.participant_ids))
    participants.sort()  # Consistent ordering

    # Generate group name if not provided
    group_name = payload.name or f"DM ({', '.join(participants[:3])})"

    doc = {
        "workspace_id": workspace_id,
        "name": group_name,
        "participants": participants,
        "participant_count": len(participants),
        "created_by": creator_id,
        "is_archived": False,
        "message_count": 0,
        "created_at": now,
        "updated_at": now,
    }

    try:
        result = await db[Collection.DIRECT_MESSAGES].insert_one(doc)
    except PyMongoError as exc:
        raise DatabaseException("Failed to create direct message group") from exc

    doc["_id"] = result.inserted_id
    await logger.ainfo(
        "direct_message_created",
        dm_id=str(result.inserted_id),
        workspace_id=workspace_id,
        creator_id=creator_id,
        participant_count=len(participants),
    )

    return _doc_to_dm(doc)


async def get_by_id(
    workspace_id: str, dm_id: str, user_id: str, db
) -> DirectMessageResponse:
    """Get DM group by ID."""
    oid = parse_object_id(dm_id, ErrorMessage.INVALID_ID)
    try:
        doc = await db[Collection.DIRECT_MESSAGES].find_one(
            {"_id": oid, "workspace_id": workspace_id}
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to query direct message") from exc

    if not doc:
        raise NotFoundException(ErrorMessage.INVITATION_NOT_FOUND)

    # Verify user is participant
    if user_id not in doc.get("participants", []):
        raise ForbiddenException(ErrorMessage.WORKSPACE_ACCESS_DENIED)

    return _doc_to_dm(doc)


async def get_detail(
    workspace_id: str, dm_id: str, user_id: str, db
) -> DirectMessageDetailResponse:
    """Get DM group with full details."""
    oid = parse_object_id(dm_id, ErrorMessage.INVALID_ID)
    try:
        doc = await db[Collection.DIRECT_MESSAGES].find_one(
            {"_id": oid, "workspace_id": workspace_id}
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to query direct message") from exc

    if not doc:
        raise NotFoundException(ErrorMessage.INVITATION_NOT_FOUND)

    # Verify user is participant
    if user_id not in doc.get("participants", []):
        raise ForbiddenException(ErrorMessage.WORKSPACE_ACCESS_DENIED)

    return _doc_to_dm_detail(doc)


async def list_by_user(
    workspace_id: str,
    user_id: str,
    db,
    cursor: str | None = None,
    limit: int = _DEFAULT_LIMIT,
) -> DirectMessageListResponse:
    """List all DM groups for a user in workspace."""
    limit = min(limit, _MAX_LIMIT)
    query: dict = {"workspace_id": workspace_id, "participants": user_id, "is_archived": False}

    if cursor:
        cursor_oid = parse_object_id(cursor, ErrorMessage.INVALID_ID)
        query["_id"] = {"$gt": cursor_oid}

    try:
        docs = (
            await db[Collection.DIRECT_MESSAGES]
            .find(query)
            .sort("updated_at", -1)
            .limit(limit + 1)
            .to_list(limit + 1)
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to list direct messages") from exc

    has_more = len(docs) > limit
    items = [_doc_to_dm(d) for d in docs[:limit]]
    next_cursor = str(docs[limit - 1]["_id"]) if has_more else None

    return DirectMessageListResponse(items=items, next_cursor=next_cursor)


async def add_participant(
    workspace_id: str, dm_id: str, new_participant_id: str, added_by: str, db
) -> DirectMessageResponse:
    """Add a participant to DM group."""
    oid = parse_object_id(dm_id, ErrorMessage.INVALID_ID)

    try:
        doc = await db[Collection.DIRECT_MESSAGES].find_one_and_update(
            {
                "_id": oid,
                "workspace_id": workspace_id,
                "participants": {"$ne": new_participant_id},
            },
            {
                "$push": {"participants": new_participant_id},
                "$inc": {"participant_count": 1},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
            return_document=ReturnDocument.AFTER,
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to add participant to DM") from exc

    if not doc:
        raise NotFoundException(ErrorMessage.INVITATION_NOT_FOUND)

    await logger.ainfo(
        "dm_participant_added",
        dm_id=dm_id,
        workspace_id=workspace_id,
        participant_id=new_participant_id,
        added_by=added_by,
    )

    return _doc_to_dm(doc)


async def remove_participant(
    workspace_id: str, dm_id: str, participant_id: str, removed_by: str, db
) -> DirectMessageResponse:
    """Remove a participant from DM group."""
    oid = parse_object_id(dm_id, ErrorMessage.INVALID_ID)

    try:
        doc = await db[Collection.DIRECT_MESSAGES].find_one_and_update(
            {"_id": oid, "workspace_id": workspace_id},
            {
                "$pull": {"participants": participant_id},
                "$inc": {"participant_count": -1},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
            return_document=ReturnDocument.AFTER,
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to remove participant from DM") from exc

    if not doc:
        raise NotFoundException(ErrorMessage.INVITATION_NOT_FOUND)

    await logger.ainfo(
        "dm_participant_removed",
        dm_id=dm_id,
        workspace_id=workspace_id,
        participant_id=participant_id,
        removed_by=removed_by,
    )

    return _doc_to_dm(doc)
